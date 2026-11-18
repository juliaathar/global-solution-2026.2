"""Contratos de cada etapa do pipeline de voz.

Cada módulo (STT, LLM, base de conhecimento, TTS) implementa um destes
protocolos, então qualquer um pode ser trocado sem mexer no resto.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol


@dataclass
class Trecho:
    """Pedaço de texto recuperado da base de conhecimento."""
    texto: str
    fonte: str = ""


@dataclass
class Mensagem:
    papel: str  # "user" ou "assistant"
    conteudo: str


class STT(Protocol):
    nome: str

    def transcrever(self, caminho_audio: str) -> str: ...


class LLM(Protocol):
    nome: str

    def responder(self, system: str, historico: list[Mensagem], contexto: list[Trecho]) -> str: ...


class BaseConhecimento(Protocol):
    def buscar(self, pergunta: str, k: int = 3) -> list[Trecho]: ...


class TTS(Protocol):
    nome: str

    def sintetizar(self, texto: str, caminho_saida: str) -> str: ...


@dataclass
class ResultadoTurno:
    transcricao: str
    resposta_texto: str
    resposta_fala: str
    audio_saida: str
    latencias: dict[str, float] = field(default_factory=dict)
    motivo: str = ""  # llm | sem_contexto | emergencia | sem_fala
