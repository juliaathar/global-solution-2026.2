"""Agendamento da busca do robô: manual (agora) ou automático (horários fixos, por padrão 08:00 e 18:00).

Uso:
  python agendador.py agora                       # busca manual, quando a pessoa quiser
  python agendador.py servir                      # fica rodando e busca nos horários (RPA_HORARIOS)
  python agendador.py servir --horarios 07:30,12:00,19:00
  python agendador.py proximas                    # mostra as próximas execuções
Alternativa ao `servir`: deixar o cron (Linux/Mac) ou o Agendador de Tarefas (Windows) chamar
`python agendador.py agora --gatilho agendado` nos horários (veja o README).

Cada busca roda o pipeline completo (coleta web, validação, classificação, protocolo, notificação). Como o protocolo é
idempotente, repetir a busca não duplica nada. Uma busca por vez: um arquivo de lock impede execuções sobrepostas.
"""
import argparse
import json
import logging
import os
import re
import time
from datetime import datetime, timedelta

import config
import main

log = logging.getLogger("rpa.agendador")
_HHMM = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")


class ErroAgendamento(Exception):
    pass


def parse_horarios(texto: str) -> list[str]:
    """'08:00, 18:00' -> ['08:00', '18:00'] (ordenado, sem repetição). Formato inválido levanta ErroAgendamento."""
    itens = sorted({h.strip() for h in texto.split(",") if h.strip()})
    if not itens:
        raise ErroAgendamento("nenhum horário informado")
    ruins = [h for h in itens if not _HHMM.match(h)]
    if ruins:
        raise ErroAgendamento(f"horário inválido (use HH:MM): {', '.join(ruins)}")
    return itens


def proxima_execucao(agora: datetime, horarios: list[str]) -> datetime:
    """Próximo horário estritamente depois de `agora` (hoje, ou amanhã se os de hoje já passaram)."""
    candidatos = []
    for dia in (0, 1):
        base = agora.date() + timedelta(days=dia)
        for h in horarios:
            hh, mm = map(int, h.split(":"))
            candidatos.append(datetime(base.year, base.month, base.day, hh, mm))
    return min(c for c in candidatos if c > agora)


class Lock:
    """Lock por arquivo: impede duas buscas ao mesmo tempo (ex.: agendada e manual juntas)."""

    def __enter__(self):
        config.SAIDA.mkdir(parents=True, exist_ok=True)
        if config.LOCK.exists() and time.time() - config.LOCK.stat().st_mtime > config.LOCK_VALIDADE_S:
            log.warning("Lock antigo removido (mais de %ss)", config.LOCK_VALIDADE_S)
            config.LOCK.unlink(missing_ok=True)
        try:
            fd = os.open(config.LOCK, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            raise ErroAgendamento("já existe uma busca em andamento") from None
        with os.fdopen(fd, "w") as f:
            f.write(f"{os.getpid()} {datetime.now().isoformat(timespec='seconds')}")
        return self

    def __exit__(self, *exc):
        config.LOCK.unlink(missing_ok=True)


def registrar_historico(registro: dict) -> None:
    config.SAIDA.mkdir(parents=True, exist_ok=True)
    with open(config.HISTORICO, "a", encoding="utf-8") as f:
        f.write(json.dumps(registro, ensure_ascii=False) + "\n")


def executar_busca(gatilho: str = "manual", com_noticias: bool = True) -> dict:
    """Uma busca completa. Nunca levanta: devolve o registro com status 'ok', 'erro' ou 'ignorada'."""
    registro = {"gatilho": gatilho, "inicio": datetime.now().isoformat(timespec="seconds")}
    inicio = time.time()
    try:
        with Lock():
            config.USAR_NOTICIAS = com_noticias
            resultado = main.executar(config.ENTRADA)
        registro.update(status="ok", resumo=resultado["resumo"])
    except ErroAgendamento as e:
        registro.update(status="ignorada", motivo=str(e))
        log.warning("Busca %s ignorada: %s", gatilho, e)
    except Exception as e:  # uma busca com problema não derruba o serviço agendado
        registro.update(status="erro", motivo=f"{type(e).__name__}: {e}")
        log.exception("Busca %s falhou; o serviço continua", gatilho)
    registro["duracao_s"] = round(time.time() - inicio, 2)
    registrar_historico(registro)
    return registro


def servir(horarios: list[str], com_noticias=True, agora_fn=datetime.now, dormir_fn=time.sleep,
           max_execucoes: int | None = None) -> int:
    """Loop do serviço: dorme até o próximo horário, faz a busca e repete. Devolve quantas buscas fez."""
    feitas = 0
    log.info("Serviço agendado: buscas às %s", ", ".join(horarios))
    while max_execucoes is None or feitas < max_execucoes:
        alvo = proxima_execucao(agora_fn(), horarios)
        log.info("Próxima busca: %s", alvo.strftime("%d/%m/%Y %H:%M"))
        while (restante := (alvo - agora_fn()).total_seconds()) > 0:
            dormir_fn(min(restante, 30))  # acorda a cada 30 s: tolera relógio ajustado e suspensão do PC
        executar_busca("agendado", com_noticias)
        feitas += 1
    return feitas


def _args():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="comando", required=True)
    a = sub.add_parser("agora", help="busca manual, imediata")
    a.add_argument("--gatilho", default="manual", choices=["manual", "agendado"],
                   help="use 'agendado' quando o cron ou o Agendador de Tarefas chamar")
    s = sub.add_parser("servir", help="fica rodando e busca nos horários")
    s.add_argument("--horarios", default=config.HORARIOS)
    p = sub.add_parser("proximas", help="mostra as próximas execuções")
    p.add_argument("--horarios", default=config.HORARIOS)
    for sp in (a, s):
        sp.add_argument("--sem-noticias", action="store_true", help="não usa o crawler de notícias")
    return ap.parse_args()


if __name__ == "__main__":
    args = _args()
    main.configurar_log()
    try:
        if args.comando == "agora":
            reg = executar_busca(args.gatilho, not args.sem_noticias)
            print(json.dumps(reg, ensure_ascii=False, indent=2))
            raise SystemExit(0 if reg["status"] == "ok" else 1)
        horarios = parse_horarios(args.horarios)
        if args.comando == "proximas":
            t = datetime.now()
            for _ in range(4):
                t = proxima_execucao(t, horarios)
                print(t.strftime("%d/%m/%Y %H:%M"))
        else:
            servir(horarios, not args.sem_noticias)
    except ErroAgendamento as e:
        print(f"Erro: {e}")
        raise SystemExit(2)
    except KeyboardInterrupt:
        print("Serviço interrompido.")
