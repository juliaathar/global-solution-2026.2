"""Avalia o TTS: gera 10 respostas em áudio e resume as notas dos avaliadores.

    python testes/avaliar_tts.py gerar --motores edge-tts piper
    # os avaliadores ouvem audios_teste/tts/ e preenchem testes/planilha_tts.csv
    python testes/avaliar_tts.py resumir

Notas de 1 a 5 em naturalidade e clareza. Cada motor é avaliado por 3 pessoas.
`gerar` não sobrescreve uma planilha já preenchida (use --forcar para recomeçar).
"""
import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from util import (AUDIOS, EVIDENCIAS, TESTES, escrever_csv, fmt, ler_csv,  # noqa: E402
                  media, tabela_md)

from adaptacao_fala import adaptar_para_fala  # noqa: E402

PLANILHA = TESTES / "planilha_tts.csv"
AVALIADORES = ["Avaliador 1", "Avaliador 2", "Avaliador 3"]
CAMPOS_PLANILHA = ["motor", "id", "arquivo", "avaliador", "naturalidade", "clareza"]


def gerar(motores: dict, textos: list[dict], pasta: Path) -> tuple[list[dict], list[dict]]:
    """`motores` mapeia nome -> objeto TTS. Retorna (tempos, linhas da planilha)."""
    pasta.mkdir(parents=True, exist_ok=True)
    tempos, planilha = [], []
    for nome, tts in motores.items():
        for t in textos:
            arquivo = pasta / f"{nome}_{t['id']}{getattr(tts, 'extensao', '.mp3')}"
            fala = adaptar_para_fala(t["texto"])
            ini = time.perf_counter()
            tts.sintetizar(fala, str(arquivo))
            tempos.append({"motor": nome, "id": t["id"], "texto_falado": fala,
                           "sintese_s": round(time.perf_counter() - ini, 3)})
            for av in AVALIADORES:
                planilha.append({"motor": nome, "id": t["id"], "arquivo": arquivo.name, "avaliador": av,
                                 "naturalidade": "", "clareza": ""})
    return tempos, planilha


def _nota(valor: str) -> int | None:
    return int(valor) if valor.isdigit() and 1 <= int(valor) <= 5 else None


def resumir(planilha: list[dict], tempos: list[dict] | None = None) -> str:
    motores = list(dict.fromkeys(l["motor"] for l in planilha))
    linhas, pendentes = [], 0
    for m in motores:
        ls = [l for l in planilha if l["motor"] == m]
        nat = [n for l in ls if (n := _nota(l["naturalidade"]))]
        cla = [n for l in ls if (n := _nota(l["clareza"]))]
        pendentes += len(ls) * 2 - len(nat) - len(cla)
        avaliadores = len({l["avaliador"] for l in ls if _nota(l["naturalidade"]) or _nota(l["clareza"])})
        sintese = media([float(t["sintese_s"]) for t in (tempos or []) if t["motor"] == m])
        linhas.append([m, avaliadores, len(nat), fmt(media(nat), 2), fmt(media(cla), 2), fmt(sintese, 2)])
    out = ["# TTS: resultados\n",
           tabela_md(["Motor", "Avaliadores", "Notas de naturalidade", "Naturalidade média (1-5)",
                      "Clareza média (1-5)", "Síntese média (s)"], linhas)]
    if pendentes:
        out.append(f"\nAtenção: {pendentes} notas ainda vazias ou inválidas (use inteiros de 1 a 5).")
    return "\n".join(out)


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    g = sub.add_parser("gerar")
    g.add_argument("--motores", nargs="+", default=["edge-tts"])
    g.add_argument("--forcar", action="store_true")
    sub.add_parser("resumir")
    a = ap.parse_args()

    if a.cmd == "gerar":
        if PLANILHA.exists() and not a.forcar:
            print(f"{PLANILHA.name} já existe e pode ter notas. Use --forcar para recomeçar.")
            return 1
        from tts import criar_tts
        textos = ler_csv(TESTES / "respostas_tts.csv")
        tempos, planilha = gerar({m: criar_tts(m) for m in a.motores}, textos, AUDIOS / "tts")
        escrever_csv(EVIDENCIAS / "tts_tempos.csv", tempos)
        escrever_csv(PLANILHA, planilha, CAMPOS_PLANILHA)
        print(f"{len(tempos)} áudios em audios_teste/tts. Planilha para os avaliadores: {PLANILHA}")
        return 0

    if not PLANILHA.exists():
        print(f"{PLANILHA.name} não existe. Rode antes: python testes/avaliar_tts.py gerar")
        return 1
    tempos_csv = EVIDENCIAS / "tts_tempos.csv"
    texto = resumir(ler_csv(PLANILHA), ler_csv(tempos_csv) if tempos_csv.exists() else None)
    (EVIDENCIAS / "tts_resumo.md").write_text(texto, encoding="utf-8")
    print(texto)
    return 0


if __name__ == "__main__":
    sys.exit(main())
