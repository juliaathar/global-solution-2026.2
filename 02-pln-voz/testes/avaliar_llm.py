"""Avalia o LLM com as 30 perguntas de testes/perguntas_llm.csv.

    python testes/avaliar_llm.py --llm ollama:qwen2.5:3b --llm groq:llama-3.1-8b-instant

Cada `conversa` usa um Assistente novo, então as perguntas de continuação têm memória.
Métricas: % de respostas corretas (normal + continuação), % de recusas adequadas
(fora do escopo) e % de abstenção adequada (dentro do tema, sem dado na base).

A correção automática confere palavras-chave: `;` significa E, `|` significa OU
(sem diferença de acento ou caixa). Ela é uma aproximação: confira a coluna
`acerto_manual` do CSV, que o grupo pode preencher (1 ou 0) e que prevalece.
"""
import argparse
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from util import (EVIDENCIAS, TESTES, escrever_csv, fmt, ler_csv, media,  # noqa: E402
                  pct, sem_acento, tabela_md)

from llm import Assistente  # noqa: E402

_RECUSA = re.compile(r"nao sei|nao tenho|nao posso|nao consigo|nao e possivel|fora do (meu )?tema|"
                     r"nao tenho essa informacao|so posso ajudar|posso ajudar com")
MOTIVOS_RECUSA = {"sem_contexto", "emergencia"}


def eh_recusa(resposta: str, motivo: str) -> bool:
    return motivo in MOTIVOS_RECUSA or bool(_RECUSA.search(sem_acento(resposta)))


def satisfaz(resposta: str, esperado: str) -> bool:
    """`a|b;c` = (a OU b) E c, ignorando acento e caixa. Esperado vazio = sem exigência."""
    r = sem_acento(resposta)
    return all(any(sem_acento(alt.strip()) in r for alt in grupo.split("|"))
               for grupo in esperado.split(";") if grupo.strip())


def julgar(tipo: str, esperado: str, resposta: str, motivo: str) -> bool:
    recusou = eh_recusa(resposta, motivo)
    if tipo in ("fora_escopo", "sem_resposta"):
        return recusou
    return satisfaz(resposta, esperado) and not recusou


def executar(llm, base, linhas: list[dict], ao_terminar=None) -> list[dict]:
    """`ao_terminar(resultado)` é chamado após cada pergunta (para gravar o progresso). Um erro do LLM
    (tempo esgotado, serviço fora do ar) vira um resultado com motivo "erro" e a rodada continua."""
    conversas: dict[str, list[dict]] = {}
    for l in linhas:
        conversas.setdefault(l["conversa"], []).append(l)
    resultados = []
    for turnos in conversas.values():
        assistente = Assistente(llm, base)
        for l in sorted(turnos, key=lambda x: int(x["turno"])):
            t = time.perf_counter()
            try:
                resposta = assistente.perguntar(l["pergunta"])
                motivo = assistente.ultimo_motivo
                acertou = int(julgar(l["tipo"], l["esperado"], resposta, motivo))
            except Exception as erro:  # noqa: BLE001 - uma falha do LLM não pode perder a rodada inteira
                resposta, motivo, acertou = f"[ERRO: {type(erro).__name__}]", "erro", 0
                print(f"  {l['id']}: erro do LLM ({type(erro).__name__}); segue para a próxima", file=sys.stderr)
            dt = time.perf_counter() - t
            resultados.append({**l, "modelo": llm.nome, "resposta": resposta, "motivo": motivo,
                               "acerto_auto": acertou, "acerto_manual": "", "obs_manual": "",
                               "latencia_s": round(dt, 3)})
            if ao_terminar:
                ao_terminar(resultados[-1])
    return resultados


def conversas_completas(resultados: list[dict], linhas: list[dict]) -> set[str]:
    """Conversas cujos turnos estão todos nos resultados e sem erro do LLM (as demais são refeitas na retomada)."""
    esperadas: dict[str, set[str]] = {}
    for l in linhas:
        esperadas.setdefault(l["conversa"], set()).add(l["id"])
    feitas: dict[str, set[str]] = {}
    for r in resultados:
        if r["motivo"] != "erro":
            feitas.setdefault(r["conversa"], set()).add(r["id"])
    return {c for c, ids in esperadas.items() if feitas.get(c, set()) >= ids}


def carregar_resultados(caminho: Path) -> list[dict]:
    """Relê o CSV de resultados (com `acerto_manual` e `obs_manual` preenchidos pelo grupo)."""
    rs = ler_csv(caminho)
    for r in rs:
        r["latencia_s"] = float(r["latencia_s"])
        r["acerto_auto"] = int(r["acerto_auto"])
    return rs


def acerto(r: dict) -> bool:
    return bool(int(r["acerto_manual"])) if str(r.get("acerto_manual", "")).strip() in ("0", "1") \
        else bool(int(r["acerto_auto"]))


def taxa(rs: list[dict]) -> float:
    return sum(acerto(r) for r in rs) / len(rs) if rs else float("nan")


def resumir(resultados: list[dict]) -> str:
    modelos = list(dict.fromkeys(r["modelo"] for r in resultados))
    linhas = []
    for m in modelos:
        rs = [r for r in resultados if r["modelo"] == m]
        por = lambda *tipos: [r for r in rs if r["tipo"] in tipos]  # noqa: E731
        linhas.append([m, len(rs), pct(taxa(por("normal", "continuacao"))), pct(taxa(por("normal"))),
                       pct(taxa(por("continuacao"))), pct(taxa(por("fora_escopo"))),
                       pct(taxa(por("sem_resposta"))), fmt(media([r["latencia_s"] for r in rs if r["motivo"] == "llm"]), 2)])
    cab = ["Modelo", "Perguntas", "% corretas (normal+cont.)", "% normais", "% continuação",
           "% recusas adequadas (fora do escopo)", "% abstenção (sem dado)", "Latência média por chamada ao LLM (s)"]
    erros = [r for r in resultados if not acerto(r)]
    out = ["# LLM: resultados\n", tabela_md(cab, linhas), "\n## Erros para análise\n",
           tabela_md(["Modelo", "Id", "Tipo", "Pergunta", "Resposta"],
                     [[r["modelo"], r["id"], r["tipo"], r["pergunta"], r["resposta"][:160]] for r in erros])
           if erros else "Nenhum erro."]
    return "\n".join(out)


def main() -> int:
    from componentes import carregar_base
    from config import LLM_API_KEY
    from llm import criar_llm
    ap = argparse.ArgumentParser()
    ap.add_argument("--llm", action="append", default=[], help="provedor:modelo (repita para comparar)")
    ap.add_argument("--perguntas", type=Path, default=TESTES / "perguntas_llm.csv")
    ap.add_argument("--anexar", action="store_true",
                    help="mantém os resultados de outros modelos (e as notas manuais) já gravados")
    ap.add_argument("--retomar", action="store_true",
                    help="continua uma rodada interrompida: pula as conversas já concluídas (sem erro). Implica --anexar")
    ap.add_argument("--so-resumir", action="store_true",
                    help="não chama o LLM: recalcula o resumo a partir do CSV, com o acerto_manual preenchido")
    ap.add_argument("--saida", type=Path, default=EVIDENCIAS, help="pasta dos resultados")
    a = ap.parse_args()
    a.saida.mkdir(parents=True, exist_ok=True)
    destino = a.saida / "llm_resultados.csv"

    if a.so_resumir:
        resultados = carregar_resultados(destino)
    else:
        if not a.llm:
            ap.error("informe --llm provedor:modelo (ou use --so-resumir)")
        linhas = ler_csv(a.perguntas)
        resultados = carregar_resultados(destino) if (a.anexar or a.retomar) and destino.exists() else []
        for spec in a.llm:
            prov, modelo = spec.split(":", 1)
            llm = criar_llm(prov, modelo, LLM_API_KEY)
            outros = [r for r in resultados if r["modelo"] != llm.nome]
            proprios = [r for r in resultados if r["modelo"] == llm.nome] if a.retomar else []
            feitas = conversas_completas(proprios, linhas)
            proprios = [r for r in proprios if r["conversa"] in feitas]
            pendentes = [l for l in linhas if l["conversa"] not in feitas]
            if feitas:
                print(f"{llm.nome}: retomando, {len(feitas)} conversas já concluídas, {len(pendentes)} perguntas a fazer")
            novos: list[dict] = []

            def gravar_progresso(r, outros=outros, proprios=proprios, novos=novos):
                novos.append(r)
                _gravar(destino, outros + proprios + novos)  # se a máquina parar, nada se perde

            executar(llm, carregar_base(), pendentes, ao_terminar=gravar_progresso)
            resultados = outros + proprios + novos
    _gravar(destino, resultados)
    print((a.saida / "llm_resumo.md").read_text(encoding="utf-8"))
    return 0


def _gravar(destino: Path, resultados: list[dict]) -> None:
    """Grava CSV e resumo de uma vez (por arquivo temporário, para não deixar um CSV pela metade)."""
    campos = list(dict.fromkeys(k for r in resultados for k in r))
    tmp = destino.with_suffix(".tmp")
    escrever_csv(tmp, resultados, campos)
    tmp.replace(destino)
    (destino.parent / "llm_resumo.md").write_text(resumir(resultados), encoding="utf-8")


if __name__ == "__main__":
    sys.exit(main())
