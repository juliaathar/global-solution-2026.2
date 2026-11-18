"""Gera áudios SINTÉTICOS para validar o pipeline de STT antes das gravações reais do grupo.

    python testes/gerar_audios_sinteticos.py          # 20 áudios de STT (3 vozes, 5 com ruído)
    python testes/gerar_audios_sinteticos.py --e2e    # 30 falas das 10 conversas do ponta a ponta

ATENÇÃO: isto NÃO substitui os 20 áudios gravados pelo grupo que o enunciado exige.
Vozes de TTS são limpas e regulares, então o WER medido aqui tende a ser mais baixo do
que com pessoas reais, e não diz nada sobre sotaque ou idade. Serve para conferir que
o script de WER funciona e para ter uma medição preliminar, rotulada como tal.

Usa as 3 vozes pt-BR do edge-tts (nuvem: o texto das frases de teste vai à Microsoft) e
mistura ruído branco (SNR de 10 dB) nos áudios marcados `ruido = sim` do manifesto.
Saída: audios_teste/sintetico/ (WAV 16 kHz mono e manifesto.csv).
"""
import asyncio
import sys
import wave
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from util import AUDIOS, escrever_csv, ler_csv  # noqa: E402

VOZES = {"A": ("Francisca", "pt-BR-FranciscaNeural"),
         "B": ("Antonio", "pt-BR-AntonioNeural"),
         "C": ("Thalita", "pt-BR-ThalitaMultilingualNeural")}
SNR_DB = 10
TAXA = 16000


def decodificar(caminho_mp3: Path) -> np.ndarray:
    """MP3 -> float32 mono 16 kHz, usando o PyAV que já vem com o faster-whisper."""
    import av
    amostras = []
    with av.open(str(caminho_mp3)) as c:
        rs = av.AudioResampler(format="s16", layout="mono", rate=TAXA)
        for frame in c.decode(audio=0):
            for f in rs.resample(frame):
                amostras.append(f.to_ndarray().reshape(-1))
    return np.concatenate(amostras).astype(np.float32) / 32768.0


def com_ruido(x: np.ndarray, snr_db: float, semente: int) -> np.ndarray:
    ruido = np.random.default_rng(semente).standard_normal(len(x)).astype(np.float32)
    p_sinal = float(np.mean(x ** 2))
    p_ruido = p_sinal / (10 ** (snr_db / 10))
    y = x + ruido * np.sqrt(p_ruido / float(np.mean(ruido ** 2)))
    return np.clip(y, -1, 1)


def salvar_wav(caminho: Path, x: np.ndarray) -> None:
    with wave.open(str(caminho), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(TAXA)
        w.writeframes((x * 32767).astype(np.int16).tobytes())


async def _sintetizar(texto: str, voz: str, destino: Path) -> None:
    import edge_tts
    await edge_tts.Communicate(texto, voz).save(str(destino))


def gerar_e2e() -> int:
    """Sintetiza as 30 falas de testes/conversas_e2e.csv (sem ruído), uma voz por conversa."""
    from util import TESTES
    saida = AUDIOS / "sintetico_e2e"
    saida.mkdir(parents=True, exist_ok=True)
    vozes = list(VOZES.values())
    for l in ler_csv(TESTES / "conversas_e2e.csv"):
        nome, voz = vozes[int(l["conversa"][1:]) % len(vozes)]
        mp3 = saida / (Path(l["arquivo"]).stem + ".mp3")
        asyncio.run(_sintetizar(l["pergunta_planejada"], voz, mp3))
        x = decodificar(mp3)
        mp3.unlink()
        salvar_wav(saida / l["arquivo"], x)
        print(f"{l['arquivo']}  {nome:9s}  {len(x) / TAXA:.1f}s")
    return 0


def main() -> int:
    if "--e2e" in sys.argv:
        return gerar_e2e()
    saida = AUDIOS / "sintetico"
    saida.mkdir(parents=True, exist_ok=True)
    manifesto = ler_csv(AUDIOS / "manifesto_stt.csv")
    novas = []
    for i, l in enumerate(manifesto):
        nome, voz = VOZES[l["falante"]]
        mp3 = saida / (Path(l["arquivo"]).stem + ".mp3")
        asyncio.run(_sintetizar(l["referencia"], voz, mp3))
        x = decodificar(mp3)
        mp3.unlink()
        if l["ruido"] == "sim":
            x = com_ruido(x, SNR_DB, semente=i)
        salvar_wav(saida / l["arquivo"], x)
        novas.append({**l, "falante": nome, "faixa_etaria": "sintetica", "sotaque": "sintetico"})
        print(f"{l['arquivo']}  {nome:9s} ruido={l['ruido']}  {len(x) / TAXA:.1f}s")
    escrever_csv(saida / "manifesto.csv", novas)
    return 0


if __name__ == "__main__":
    sys.exit(main())
