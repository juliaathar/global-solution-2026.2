"""Schemas (Pydantic) do endpoint do motor RAG (disciplina 03)."""
from typing import Literal

from pydantic import BaseModel, Field


class Turno(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=2000)


class PerguntaRAG(BaseModel):
    pergunta: str = Field(min_length=2, max_length=500)
    historico: list[Turno] = Field(default_factory=list, max_length=10)


class FonteRAG(BaseModel):
    titulo: str
    url: str
    data_consulta: str


class RespostaRAG(BaseModel):
    resposta: str
    fontes: list[FonteRAG]
    abstencao: bool            # sem evidência suficiente nas fontes
    bloqueada: bool            # pedido recusado pelo filtro de entrada
    esclarecimento: bool       # pergunta vaga: o assistente pediu mais detalhes
    saida_bloqueada: str = ""  # motivo, se a guarda de saída barrou a resposta do LLM
