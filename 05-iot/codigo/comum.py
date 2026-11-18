"""Constantes e utilitários compartilhados pelos scripts do OuviAí."""
import hashlib
import os
import wave
from pathlib import Path

import numpy as np

RAIZ = Path(__file__).resolve().parent.parent
DADOS = Path(os.getenv("OUVIAI_DADOS", RAIZ / "dados_audio"))  # a variável serve só para testes
BRUTOS = DADOS / "brutos"            # o que vocês gravaram, uma pasta por classe (não versionado)
PREPARADOS = DADOS / "preparados"    # 16 kHz, mono, PCM16, 5 s, prontos para o Edge Impulse
MANIFESTO = DADOS / "manifesto.csv"
EVIDENCIAS = Path(os.getenv("OUVIAI_EVIDENCIAS", RAIZ / "evidencias"))

CLASSES = ("campainha", "batida_porta", "ambiente")
TAXA = 16000
DURACAO_S = 5.0
POR_CLASSE = 20
TREINO, TESTE = 15, 5
SEMENTE = 42


def ler_wav(caminho: Path) -> tuple[np.ndarray, int, int, int]:
    """Devolve (amostras int16 mono, taxa, canais originais, bits originais)."""
    with wave.open(str(caminho), "rb") as w:
        canais, largura, taxa, n = w.getnchannels(), w.getsampwidth(), w.getframerate(), w.getnframes()
        bruto = w.readframes(n)
    if largura != 2:
        raise ValueError(f"{caminho.name}: {largura * 8} bits (esperado 16)")
    x = np.frombuffer(bruto, dtype="<i2")
    if canais > 1:
        x = x.reshape(-1, canais).mean(axis=1).astype(np.int16)
    return x, taxa, canais, largura * 8


def gravar_wav(caminho: Path, amostras: np.ndarray, taxa: int = TAXA) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(caminho), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(taxa)
        w.writeframes(amostras.astype("<i2").tobytes())


def niveis_dbfs(x: np.ndarray) -> tuple[float, float]:
    """(pico, RMS) em dBFS. -inf vira -120."""
    f = x.astype(np.float64) / 32768.0
    pico = np.max(np.abs(f)) if f.size else 0.0
    rms = np.sqrt(np.mean(f ** 2)) if f.size else 0.0
    return (round(20 * np.log10(pico), 1) if pico > 0 else -120.0,
            round(20 * np.log10(rms), 1) if rms > 0 else -120.0)


def sha1_amostras(x: np.ndarray) -> str:
    return hashlib.sha1(x.astype("<i2").tobytes()).hexdigest()[:16]
