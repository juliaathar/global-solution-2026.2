"""Ponto de entrada do robô RPA do EloBairro.

Uso: python main.py [--entrada caminho.csv]
Fluxo: ingestão, validação, deduplicação, classificação, protocolo, notificação, relatório.
"""
import argparse
import csv
import json
import logging
import time
from pathlib import Path

import config
from armazenamento import Armazenamento
from classificador import classificar
from coleta_noticias import coletar_relatos_publicos
from enriquecimento import Enriquecedor
from privacidade import mascarar
from deduplicacao import eh_duplicado, normalizar
from ingestao import ler_relatos
from notificador import enviar_com_retry
from validacao import validar


def configurar_log():
    config.SAIDA.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        handlers=[logging.FileHandler(config.LOG, encoding="utf-8"), logging.StreamHandler()],
    )


def executar(entrada: Path, enviar_fn=None) -> dict:
    inicio = time.time()
    log = logging.getLogger("rpa.main")
    config.SAIDA.mkdir(parents=True, exist_ok=True)
    relatos = ler_relatos(entrada)
    noticias_info = {}
    if config.USAR_NOTICIAS:
        publicos, noticias_info = coletar_relatos_publicos()
        relatos += publicos
    banco = Armazenamento(config.BANCO)
    vistos: list[str] = []
    resumo = {"lidos": len(relatos), "protocolos": 0, "invalidos": 0, "duplicados": 0,
              "ja_processados": 0, "revisao_humana": 0, "notificacoes_falhas": 0,
              "dados_pessoais_mascarados": 0, "ubs_origem": "", "inmet_origem": "", "avisos_vigentes": 0,
              "noticias_publicas": noticias_info.get("relevantes", 0),
              "noticias_origem": noticias_info.get("origem", "")}
    detalhes, revisao = [], []
    extra = {"enviar_fn": enviar_fn} if enviar_fn else {}
    enriquecedor = Enriquecedor(resumo)

    for r in relatos:
        try:
            rid = r.get("id", "")
            ok, motivo = validar(r)
            if not ok:
                resumo["invalidos"] += 1
                log.warning("Relato %s invalido: %s", rid or "?", motivo)
                continue
            if banco.existe(rid):
                resumo["ja_processados"] += 1
                continue
            texto, n_mascarados = mascarar(r["texto"])  # a partir daqui só o texto mascarado circula
            resumo["dados_pessoais_mascarados"] += n_mascarados
            if eh_duplicado(texto, vistos, config.SIMILARIDADE_DUPLICADO):
                resumo["duplicados"] += 1
                log.info("Relato %s duplicado", rid)
                continue
            vistos.append(normalizar(texto))
            c = classificar(texto)
            if c["confianca"] < config.CONFIANCA_MINIMA:
                resumo["revisao_humana"] += 1
                revisao.append({"id": rid, "texto": texto, **c})
                continue
            alerta = enriquecedor.aviso_inmet(c)
            if alerta:
                c = {**c, "urgencia": "alta"}  # antes de gravar, para o banco guardar a urgência final
            encaminhamento = enriquecedor.encaminhamento(texto, c)
            protocolo = banco.salvar(rid, c["categoria"], c["urgencia"], c["confianca"])
            resumo["protocolos"] += 1
            if not enviar_com_retry(protocolo, config.TENTATIVAS, config.ESPERA_BASE_S, **extra):
                resumo["notificacoes_falhas"] += 1
            detalhes.append({"id": rid, "protocolo": protocolo, "encaminhamento": encaminhamento,
                             "alerta_inmet": alerta, **c,
                             "categoria_real": r.get("categoria_real", ""),
                             "urgencia_real": r.get("urgencia_real", "")})
        except Exception:  # um relato com problema nunca derruba a execução inteira
            log.exception("Erro inesperado no relato %s; seguindo", r.get("id"))
            resumo["invalidos"] += 1

    banco.fechar()
    if revisao:
        with open(config.REVISAO, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(revisao[0]))
            w.writeheader()
            w.writerows(revisao)
    resumo["duracao_s"] = round(time.time() - inicio, 3)
    config.RELATORIO.write_text(
        json.dumps({"resumo": resumo, "protocolos": detalhes}, ensure_ascii=False, indent=2), encoding="utf-8")
    log.info("Resumo: %s", resumo)
    return {"resumo": resumo, "protocolos": detalhes}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--entrada", type=Path, default=config.ENTRADA)
    args = ap.parse_args()
    configurar_log()
    executar(args.entrada)
