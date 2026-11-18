"""Voz: pergunta falada -> STT (02) -> motor RAG (03) -> adaptação para fala (02) -> TTS (02)."""
import os

from fastapi import APIRouter, File, HTTPException, UploadFile
from requests import RequestException

from api.providers import voz_provider as vz
from api.schemas.voz import AudioFala, PedidoFala, RespostaVoz

router = APIRouter(prefix="/voz", tags=["voz"])

MAX_AUDIO = 5 * 1024 * 1024  # cerca de 30 s de fala em WAV 16 kHz
EXT_AUDIO = {".wav", ".mp3", ".webm", ".ogg", ".m4a"}


def _falar(texto: str) -> tuple[str, str, str]:
    fala = vz.adaptar_para_fala(texto)
    try:
        audio, formato = vz.sintetizar(fala)
    except vz.VozIndisponivel:
        audio, formato = "", ""  # o texto continua na tela; só o áudio fica de fora
    return fala, audio, formato


@router.post("/perguntar", response_model=RespostaVoz)
async def perguntar(arquivo: UploadFile = File(...)):
    ext = os.path.splitext(arquivo.filename or "")[1].lower() or ".wav"
    if ext not in EXT_AUDIO:
        raise HTTPException(415, "Formato de áudio não suportado. Use WAV, MP3, WEBM, OGG ou M4A.")
    dados = await arquivo.read(MAX_AUDIO + 1)
    if not dados:
        raise HTTPException(422, "Áudio vazio.")
    if len(dados) > MAX_AUDIO:
        raise HTTPException(413, "Áudio muito longo. Fale por até 30 segundos.")
    try:
        transcricao = vz.transcrever(dados, ext)
    except vz.VozIndisponivel as e:
        raise HTTPException(503, str(e))
    if not transcricao.strip():
        return RespostaVoz(transcricao="", resposta="Não consegui ouvir. Pode repetir, por favor?",
                           resposta_fala="Não consegui ouvir. Pode repetir, por favor?")
    try:
        from api.routers.rag import responder  # motor RAG da pasta 03
        r = responder(transcricao, [])
    except ImportError:
        raise HTTPException(503, "O motor de respostas não está instalado.")
    except RequestException:
        raise HTTPException(503, "O assistente está indisponível no momento. Tente de novo ou ligue 156.")
    fala, audio, formato = _falar(r["resposta"])
    return RespostaVoz(transcricao=transcricao, resposta=r["resposta"], resposta_fala=fala, audio_base64=audio,
                       formato_audio=formato, fontes=r["fontes"], abstencao=r["abstencao"])


@router.post("/falar", response_model=AudioFala, summary="Lê em voz alta um texto da tela (acessibilidade)")
def falar(pedido: PedidoFala):
    try:
        fala = vz.adaptar_para_fala(pedido.texto)
        audio, formato = vz.sintetizar(fala)
    except (vz.VozIndisponivel, ImportError) as e:
        raise HTTPException(503, str(e) or "Síntese de voz indisponível.")
    return AudioFala(texto_falado=fala, audio_base64=audio, formato_audio=formato)
