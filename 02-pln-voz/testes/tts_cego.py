"""Avaliação cega do TTS: os avaliadores não sabem qual motor (Piper ou edge-tts) estão ouvindo.

    python testes/tts_cego.py preparar     # cria audios_teste/tts_cego/aval_01.wav ... e as planilhas
    python testes/tts_cego.py consolidar   # passa as notas para testes/planilha_tts.csv
    python testes/avaliar_tts.py resumir   # (depois) tabela de notas por motor

`preparar` embaralha os 20 áudios (semente fixa), converte todos para WAV mono 22,05 kHz (assim o formato não
entrega o motor) e grava:
  * testes/tts_cego_notas.csv: o que os avaliadores preenchem (aval, avaliador, naturalidade, clareza);
  * testes/tts_cego_chave.csv: qual aval_NN é qual motor. Não mostre aos avaliadores antes de terminarem.
Cada avaliador ouve os 20 áudios e dá notas de 1 a 5. Troque "Avaliador 1, 2 e 3" pelos nomes reais.
"""
import argparse
import random
import sys
import wave
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from util import AUDIOS, TESTES, escrever_csv, ler_csv  # noqa: E402

TAXA = 22050
PLANILHA = TESTES / "planilha_tts.csv"
NOTAS = TESTES / "tts_cego_notas.csv"
CHAVE = TESTES / "tts_cego_chave.csv"
PASTA = AUDIOS / "tts_cego"
AVALIADORES = ["Avaliador 1", "Avaliador 2", "Avaliador 3"]


def _converter(origem: Path, destino: Path) -> None:
    import av
    partes = []
    with av.open(str(origem)) as c:
        ra = av.AudioResampler(format="s16", layout="mono", rate=TAXA)
        for quadro in c.decode(audio=0):
            for q in ra.resample(quadro):
                partes.append(q.to_ndarray().reshape(-1))
        for q in ra.resample(None) or []:
            partes.append(q.to_ndarray().reshape(-1))
    destino.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(destino), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(TAXA)
        w.writeframes(np.concatenate(partes).astype("<i2").tobytes())


def preparar(planilha: Path = PLANILHA, pasta_audios: Path = AUDIOS / "tts", pasta: Path = PASTA,
             notas: Path = NOTAS, chave: Path = CHAVE, semente: int = 2026, forcar: bool = False) -> list[dict]:
    if (notas.exists() or chave.exists()) and not forcar:
        raise SystemExit(f"{notas.name} ou {chave.name} já existe: use --forcar só para recomeçar (apaga as notas).")
    arquivos = sorted({l["arquivo"]: (l["motor"], l["id"]) for l in ler_csv(planilha)}.items())
    random.Random(semente).shuffle(arquivos)
    linhas_chave, linhas_notas = [], []
    for i, (arquivo, (motor, rid)) in enumerate(arquivos, 1):
        aval = f"aval_{i:02d}"
        _converter(pasta_audios / arquivo, pasta / f"{aval}.wav")
        linhas_chave.append({"aval": aval, "arquivo": arquivo, "motor": motor, "id": rid})
        linhas_notas += [{"aval": aval, "avaliador": a, "naturalidade": "", "clareza": ""} for a in AVALIADORES]
    escrever_csv(chave, linhas_chave)
    escrever_csv(notas, linhas_notas)
    return linhas_chave


def consolidar(notas: Path = NOTAS, chave: Path = CHAVE, planilha: Path = PLANILHA) -> tuple[list[dict], list[str]]:
    """Devolve (linhas da planilha, problemas). Só grava a planilha se não houver problemas."""
    por_aval = {l["aval"]: l for l in ler_csv(chave)}
    linhas, problemas = [], []
    for l in ler_csv(notas):
        k = por_aval.get(l["aval"])
        if not k:
            problemas.append(f"{l['aval']}: não está na chave")
            continue
        for campo in ("naturalidade", "clareza"):
            if not (l[campo].isdigit() and 1 <= int(l[campo]) <= 5):
                problemas.append(f"{l['aval']} / {l['avaliador']}: {campo} precisa ser um inteiro de 1 a 5 (veio '{l[campo]}')")
        linhas.append({"motor": k["motor"], "id": k["id"], "arquivo": k["arquivo"], "avaliador": l["avaliador"],
                       "naturalidade": l["naturalidade"], "clareza": l["clareza"]})
    nomes = {l["avaliador"] for l in linhas}
    if len(nomes) < 3:
        problemas.append(f"são necessárias pelo menos 3 pessoas distintas; há {len(nomes)}")
    if any(n.startswith("Avaliador ") for n in nomes):
        problemas.append("troque 'Avaliador 1/2/3' pelos nomes reais dos avaliadores")
    if not problemas:
        escrever_csv(planilha, linhas, ["motor", "id", "arquivo", "avaliador", "naturalidade", "clareza"])
    return linhas, problemas


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("acao", choices=["preparar", "consolidar"])
    ap.add_argument("--forcar", action="store_true")
    a = ap.parse_args()
    if a.acao == "preparar":
        ch = preparar(forcar=a.forcar)
        print(f"{len(ch)} áudios em {PASTA} e planilha em {NOTAS}. Não mostre {CHAVE.name} aos avaliadores.")
        return 0
    linhas, problemas = consolidar()
    if problemas:
        print("Não consolidei:\n  " + "\n  ".join(problemas[:20]) + (f"\n  ... e mais {len(problemas) - 20}" if len(problemas) > 20 else ""))
        return 1
    print(f"{len(linhas)} notas gravadas em {PLANILHA}. Agora rode: python testes/avaliar_tts.py resumir")
    return 0


if __name__ == "__main__":
    sys.exit(main())
