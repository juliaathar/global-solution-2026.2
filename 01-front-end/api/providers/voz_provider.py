"""Liga a API ao assistente de voz (pasta 02): STT faster-whisper, adaptação para fala e TTS.

Tudo é importado só quando usado. Se as dependências de voz não estiverem instaladas, levanta
`VozIndisponivel` e a API responde 503 com uma mensagem clara, sem derrubar o resto do sistema.
"""
import base64
import os
import tempfile
from functools import lru_cache

from api.core.integracao import importar_isolado


class VozIndisponivel(RuntimeError):
    pass


@lru_cache(maxsize=1)
def _adaptar():
    return importar_isolado("voz", "adaptacao_fala").adaptar_para_fala


@lru_cache(maxsize=1)
def _stt():
    try:
        cfg = importar_isolado("voz", "config")
        modulo = importar_isolado("voz", "stt.whisper_stt")
        return modulo.WhisperSTT(cfg.STT_MODEL, apagar_audio=True)
    except ImportError as e:
        raise VozIndisponivel("Reconhecimento de fala não instalado (pip install -r 02-pln-voz/requirements.txt).") from e


@lru_cache(maxsize=1)
def _tts():
    try:
        cfg = importar_isolado("voz", "config")
        return importar_isolado("voz", "tts").criar_tts(cfg.TTS_ENGINE)
    except ImportError as e:
        raise VozIndisponivel("Síntese de voz não instalada (pip install -r 02-pln-voz/requirements.txt).") from e


def adaptar_para_fala(texto: str) -> str:
    return _adaptar()(texto)


def transcrever(dados: bytes, sufixo: str) -> str:
    """Grava num arquivo temporário só para o STT; o STT da pasta 02 apaga o arquivo depois de ler."""
    stt = _stt()
    with tempfile.NamedTemporaryFile(suffix=sufixo, delete=False) as tmp:
        tmp.write(dados)
        caminho = tmp.name
    try:
        return stt.transcrever(caminho)
    finally:
        if os.path.exists(caminho):
            os.unlink(caminho)


def sintetizar(texto_fala: str) -> tuple[str, str]:
    """Devolve (áudio em base64, formato). O arquivo temporário é apagado em seguida."""
    tts = _tts()
    ext = getattr(tts, "extensao", ".mp3")
    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
        caminho = tmp.name
    try:
        tts.sintetizar(texto_fala, caminho)
        with open(caminho, "rb") as f:
            return base64.b64encode(f.read()).decode("ascii"), ext.lstrip(".")
    except Exception as e:  # rede do edge-tts, voz Piper ausente etc.
        raise VozIndisponivel(f"Não foi possível gerar o áudio da resposta ({e.__class__.__name__}).") from e
    finally:
        os.unlink(caminho)
