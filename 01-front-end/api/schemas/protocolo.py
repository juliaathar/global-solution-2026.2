"""Schemas dos protocolos: contrato do robô RPA (pasta 06) e listagem para o painel do gestor."""
from typing import Literal, Optional

from pydantic import BaseModel, Field

from api.schemas.relato import Categoria, Regiao, Urgencia

Status = Literal["aberto", "em_analise", "resolvido"]


class ProtocoloRobo(BaseModel):
    """Contrato de 06-rpa/codigo/api_simulada.py. Só `protocolo` é obrigatório; o resto é opcional."""
    protocolo: str = Field(min_length=5, max_length=40, pattern=r"^ELB-[A-Z0-9-]+$")
    categoria: Optional[Categoria] = None
    urgencia: Optional[Urgencia] = None
    confianca: Optional[float] = Field(default=None, ge=0, le=1)
    encaminhamento: Optional[str] = Field(default=None, max_length=300)
    alerta_inmet: Optional[str] = Field(default=None, max_length=200)


class Ocorrencia(BaseModel):
    protocolo: str
    origem: Literal["app", "robo_rpa"]
    canal: str
    categoria: str
    urgencia: str
    confianca: Optional[float]
    regiao: str
    status: Status
    metodo: str
    resumo: str
    criado_em: str
    probabilidade_fissura: Optional[float] = None
    alerta_inmet: str = ""


class AtualizarStatus(BaseModel):
    status: Status


class ResultadoImportacao(BaseModel):
    arquivo: str
    importados: int
    ja_existiam: int
