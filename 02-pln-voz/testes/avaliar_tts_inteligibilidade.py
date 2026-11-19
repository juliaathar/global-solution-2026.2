"""Clareza objetiva do TTS: transcreve cada áudio sintetizado com o Whisper e mede o WER contra o texto falado.

    python testes/avaliar_tts_inteligibilidade.py --modelo small

Lê evidencias/tts_tempos.csv (motor, id, texto_falado) e os áudios de audios_teste/tts/. Grava
evidencias/tts_inteligibilidade.csv e .md.

LIMITE: mede se uma máquina reconhece a fala (inteligibilidade). Não mede naturalidade nem a clareza para uma pessoa
idosa, e não substitui as notas de 1 a 5 de pelo menos 3 pessoas pedidas pelo enunciado: é um complemento.
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from avaliar_stt import wer  # noqa: E402
from util import AUDIOS, EVIDENCIAS, escrever_csv, fmt, ler_csv, media, tabela_md  # noqa: E402


def avaliar(stt, linhas: list[dict], pasta: Path) -> list[dict]:
    """`linhas`: motor, id, texto_falado. O arquivo é `<motor>_<id>` com a extensão do motor (.mp3 ou .wav)."""
    resultados = []
    for l in linhas:
        arquivo = next(iter(sorted(pasta.glob(f"{l['motor']}_{l['id']}.*"))), None)
        if arquivo is None:
            resultados.append({**l, "arquivo": "", "transcricao": "", "wer": "", "erro": "áudio não encontrado"})
            continue
        try:
            hip = stt.transcrever(str(arquivo))
            resultados.append({**l, "arquivo": arquivo.name, "transcricao": hip,
                               "wer": round(wer(l["texto_falado"], hip), 4), "erro": ""})
        except Exception as e:  # noqa: BLE001 - um áudio com problema não derruba a medição
            resultados.append({**l, "arquivo": arquivo.name, "transcricao": "", "wer": "", "erro": type(e).__name__})
    return resultados


def resumir(resultados: list[dict], modelo: str) -> str:
    motores = list(dict.fromkeys(r["motor"] for r in resultados))
    linhas = []
    for m in motores:
        w = [float(r["wer"]) for r in resultados if r["motor"] == m and r["wer"] != ""]
        linhas.append([m, len(w), fmt(media(w), 3), fmt(max(w), 3) if w else "n/d",
                       sum(1 for x in w if x == 0)])
    piores = sorted((r for r in resultados if r["wer"] != ""), key=lambda r: -float(r["wer"]))[:5]
    return "\n".join([
        "# TTS: inteligibilidade medida pelo Whisper\n",
        f"Cada áudio sintetizado foi transcrito pelo faster-whisper `{modelo}` e comparado ao texto falado. "
        "Mede se uma máquina reconhece a fala; **não** mede naturalidade nem substitui as notas de pessoas.\n",
        tabela_md(["Motor", "Áudios", "WER médio", "WER máximo", "Áudios sem nenhum erro"], linhas),
        "\n## Cinco maiores erros\n",
        tabela_md(["Motor", "Id", "WER", "Texto falado", "Transcrição"],
                  [[r["motor"], r["id"], r["wer"], r["texto_falado"][:90], r["transcricao"][:90]] for r in piores]),
    ])


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--modelo", default="small", help="modelo do faster-whisper (base ou small)")
    ap.add_argument("--tempos", type=Path, default=EVIDENCIAS / "tts_tempos.csv")
    ap.add_argument("--pasta", type=Path, default=AUDIOS / "tts")
    ap.add_argument("--saida", type=Path, default=EVIDENCIAS)
    a = ap.parse_args()
    from stt import WhisperSTT
    stt = WhisperSTT(a.modelo, apagar_audio=False)  # áudios de TTS não são dados de ninguém: não apagar
    resultados = avaliar(stt, ler_csv(a.tempos), a.pasta)
    a.saida.mkdir(parents=True, exist_ok=True)
    escrever_csv(a.saida / "tts_inteligibilidade.csv", resultados)
    (a.saida / "tts_inteligibilidade.md").write_text(resumir(resultados, a.modelo), encoding="utf-8")
    print((a.saida / "tts_inteligibilidade.md").read_text(encoding="utf-8"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
