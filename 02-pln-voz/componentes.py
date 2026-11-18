"""Monta STT, LLM, base de conhecimento e TTS a partir do .env (ou módulos falsos no --demo).

Fica fora do app.py para que os scripts de teste não dependam do Gradio.
"""
import logging
import math
import os
import struct
import wave

from config import LLM_API_KEY, LLM_MODEL, LLM_PROVIDER, STT_MODEL, TTS_ENGINE
from llm.base_stub import BaseStub

log = logging.getLogger("componentes")


def tom_wav(caminho: str) -> None:
    with wave.open(caminho, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(16000)
        w.writeframes(b"".join(struct.pack("<h", int(8000 * math.sin(2 * math.pi * 440 * i / 16000)))
                               for i in range(4800)))


class DemoSTT:
    nome = "demo-stt"
    _falas = ["Que horas a UBS abre?", "E o que eu levo?", "Quem ganhou o jogo de futebol?"]

    def __init__(self, apagar_audio: bool = True):
        self.i = 0
        self.apagar_audio = apagar_audio

    def transcrever(self, caminho_audio: str) -> str:
        if self.apagar_audio and os.path.exists(caminho_audio):
            os.remove(caminho_audio)  # mesma retenção mínima do STT real
        fala = self._falas[self.i % len(self._falas)]
        self.i += 1
        return fala


class DemoLLM:
    nome = "demo-llm"

    def responder(self, system, historico, contexto):
        return "**Resposta simulada.** " + " ".join(t.texto for t in contexto[:1])


class DemoTTS:
    nome = "demo-tts"
    extensao = ".wav"

    def sintetizar(self, texto: str, caminho_saida: str) -> str:
        tom_wav(caminho_saida)
        return caminho_saida


def carregar_base():
    """Base de conhecimento. Padrão: o RAG da pasta 03 (BASE_CONHECIMENTO=rag). Se ele não puder ser
    carregado (falta fastembed, modelo de embeddings sem rede), cai na base fictícia de exemplo e AVISA:
    as respostas dela não são oficiais. BASE_CONHECIMENTO=stub força a base fictícia (testes)."""
    if os.getenv("BASE_CONHECIMENTO", "rag").lower() == "stub":
        return BaseStub()
    try:
        from llm.base_rag import BaseRAG
        return BaseRAG()
    except Exception as e:  # noqa: BLE001 - qualquer falha de carga cai no caminho seguro
        log.warning("RAG da pasta 03 indisponível (%s: %s). Usando a base FICTÍCIA de exemplo; "
                    "as respostas não são oficiais.", type(e).__name__, e)
        return BaseStub()


def carregar_componentes(demo: bool, apagar_audio: bool = True):
    """Retorna (stt, llm, base, tts). `apagar_audio=False` é só para os scripts de teste."""
    if demo:
        return DemoSTT(apagar_audio), DemoLLM(), BaseStub(), DemoTTS()
    from llm import criar_llm
    from stt import WhisperSTT
    from tts import criar_tts
    return (WhisperSTT(STT_MODEL, apagar_audio=apagar_audio),
            criar_llm(LLM_PROVIDER, LLM_MODEL, LLM_API_KEY),
            carregar_base(), criar_tts(TTS_ENGINE))
