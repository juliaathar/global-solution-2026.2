from pydantic import BaseModel, Field

from api.schemas.rag import FonteRAG


class RespostaVoz(BaseModel):
    transcricao: str
    resposta: str
    resposta_fala: str = Field(description="Texto adaptado para fala (pasta 02)")
    audio_base64: str = Field(default="", description="Áudio da resposta; vazio se o TTS falhou")
    formato_audio: str = ""
    fontes: list[FonteRAG] = Field(default_factory=list)
    abstencao: bool = False


class PedidoFala(BaseModel):
    texto: str = Field(min_length=1, max_length=1500)


class AudioFala(BaseModel):
    texto_falado: str
    audio_base64: str
    formato_audio: str
