from typing import List

from pydantic import BaseModel, Field


class PredicaoImagem(BaseModel):
    rotulo: str = Field(description="sem_fissura ou com_fissura")
    confianca: float = Field(ge=0, le=1, description="Confiança do modelo no rótulo devolvido")
    probabilidade_fissura: float = Field(ge=0, le=1)
    inspecao_recomendada: bool
    limiar: float
    latencia_ms: float
    aviso: str


class QuadroResultado(BaseModel):
    indice: int
    tempo_s: float
    probabilidade_fissura: float
    alerta: bool


class PredicaoVideo(BaseModel):
    quadros_analisados: int
    quadros_com_alerta: int
    percentual_alertas: float
    latencia_media_ms: float
    fps_processamento: float
    resolucao_original: str
    passo_amostragem: int
    limiar: float
    aviso: str
    quadros: List[QuadroResultado]
