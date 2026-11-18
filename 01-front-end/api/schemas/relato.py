"""Schemas do relato de problema do bairro: entrada do cidadão, proposta da IA e confirmação humana."""
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator

from api.core.config import TEXTO_MAX, TEXTO_MIN

Categoria = Literal["buraco", "iluminacao", "lixo", "calcada", "alagamento", "servico_saude", "indefinido"]
Urgencia = Literal["baixa", "media", "alta"]
Regiao = Literal["Centro", "Norte", "Sul", "Leste", "Oeste", "Sudeste", "Não informada"]
Origem = Literal["texto", "voz", "foto"]


class EvidenciaFoto(BaseModel):
    """Resultado da visão computacional (pasta 04) que o front repassa junto com o relato."""
    probabilidade_fissura: float = Field(ge=0, le=1)
    inspecao_recomendada: bool


class RelatoEntrada(BaseModel):
    texto: str = Field(min_length=TEXTO_MIN, max_length=TEXTO_MAX,
                       description="Descrição do problema, com uma referência de lugar")
    regiao: Regiao = "Não informada"
    origem: Origem = "texto"
    foto: Optional[EvidenciaFoto] = None

    @field_validator("texto")
    @classmethod
    def sem_so_espacos(cls, v: str) -> str:
        v = " ".join(v.split())
        if len(v) < TEXTO_MIN:
            raise ValueError(f"Escreva pelo menos {TEXTO_MIN} letras contando o que aconteceu.")
        return v


class EstruturaLLM(BaseModel):
    """Formato exigido do LLM. Qualquer resposta fora dele é descartada e o sistema usa as regras."""
    categoria: Categoria
    urgencia: Urgencia
    resumo: str = Field(min_length=5, max_length=200)


class PropostaRelato(BaseModel):
    """O que a IA entendeu. Nada é registrado até o cidadão confirmar (human-in-the-loop)."""
    texto_mascarado: str
    dados_pessoais_mascarados: int = Field(ge=0)
    categoria: Categoria
    categoria_rotulo: str
    urgencia: Urgencia
    confianca: float = Field(ge=0, le=1)
    resumo: str
    encaminhamento: str
    metodo: Literal["llm", "regras"]
    precisa_revisao: bool
    avisos: list[str] = Field(default_factory=list)
    regiao: Regiao
    origem: Origem
    duplicado_de: Optional[str] = None  # protocolo já aberto para um relato muito parecido


class ConfirmacaoRelato(BaseModel):
    confirmado: Literal[True] = Field(description="O cidadão leu e concordou com a proposta")
    texto_mascarado: str = Field(min_length=TEXTO_MIN, max_length=TEXTO_MAX)
    categoria: Categoria
    urgencia: Urgencia
    confianca: float = Field(ge=0, le=1)
    metodo: Literal["llm", "regras"]
    regiao: Regiao = "Não informada"
    origem: Origem = "texto"
    corrigido_pelo_cidadao: bool = False
    probabilidade_fissura: Optional[float] = Field(default=None, ge=0, le=1)


class ProtocoloCriado(BaseModel):
    protocolo: str
    novo: bool
    categoria_rotulo: str
    urgencia: Urgencia
    encaminhamento: str
    proximo_passo: str
    status: str
