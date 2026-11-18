"""Schemas dos eventos sonoros vindos do OuviAí (pasta 05, Edge Impulse)."""
from typing import Literal, Optional

from pydantic import BaseModel, Field

ClasseSom = Literal["campainha", "batida_porta", "ambiente"]


class EventoSom(BaseModel):
    classe: ClasseSom
    confianca: float = Field(ge=0, le=1)
    dispositivo: str = Field(default="celular", min_length=1, max_length=40, pattern=r"^[\w .-]+$")
    # Nunca áudio: a ponte manda só a classe e a confiança. Conversas não saem do aparelho.


class AlertaSom(BaseModel):
    id: int
    classe: ClasseSom
    confianca: float
    dispositivo: str
    virou_alerta: bool
    mensagem: str
    icone: str
    motivo: str
    criado_em: str
    limiar: float
    vibracao_ms: Optional[list[int]] = None
