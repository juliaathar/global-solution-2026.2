import io
import os
import tempfile

from fastapi import APIRouter, File, HTTPException, Query, UploadFile
from PIL import Image, UnidentifiedImageError

from api.providers import visao_provider as vp
from api.schemas.visao import PredicaoImagem, PredicaoVideo

router = APIRouter(prefix="/visao", tags=["visao-computacional"])

MAX_IMAGEM = 5 * 1024 * 1024
MAX_VIDEO = 50 * 1024 * 1024
TIPOS_IMAGEM = {"image/jpeg", "image/png"}
EXT_VIDEO = {".mp4", ".avi", ".mov", ".mkv"}


async def _ler(arquivo: UploadFile, limite: int) -> bytes:
    dados = await arquivo.read(limite + 1)
    if not dados:
        raise HTTPException(422, "Arquivo vazio.")
    if len(dados) > limite:
        raise HTTPException(413, f"Arquivo maior que {limite // (1024 * 1024)} MB.")
    return dados


@router.post("/imagem", response_model=PredicaoImagem)
async def classificar_imagem(
    arquivo: UploadFile = File(...),
    limiar: float = Query(None, ge=0.05, le=0.95, description="Limiar de P(fissura) para recomendar inspeção"),
):
    if arquivo.content_type not in TIPOS_IMAGEM:
        raise HTTPException(415, "Formato não suportado. Envie JPG ou PNG.")
    dados = await _ler(arquivo, MAX_IMAGEM)
    try:
        img = Image.open(io.BytesIO(dados))
        img.load()
    except (UnidentifiedImageError, OSError):
        raise HTTPException(422, "Imagem inválida ou corrompida.")
    try:
        return vp.classificar_imagem(img, limiar if limiar is not None else vp.limiar_padrao())
    except vp.ModeloIndisponivel as e:
        raise HTTPException(503, str(e))


@router.post("/video", response_model=PredicaoVideo)
async def classificar_video(
    arquivo: UploadFile = File(...),
    passo: int = Query(5, ge=1, le=60, description="Analisa 1 a cada N quadros"),
    limiar: float = Query(None, ge=0.05, le=0.95),
    max_quadros: int = Query(300, ge=1, le=600),
):
    ext = os.path.splitext(arquivo.filename or "")[1].lower()
    if ext not in EXT_VIDEO:
        raise HTTPException(415, "Formato de vídeo não suportado. Use MP4, AVI, MOV ou MKV.")
    dados = await _ler(arquivo, MAX_VIDEO)
    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
        tmp.write(dados)
        caminho = tmp.name
    try:
        return vp.classificar_video(caminho, passo, limiar if limiar is not None else vp.limiar_padrao(), max_quadros)
    except vp.ModeloIndisponivel as e:
        raise HTTPException(503, str(e))
    except ValueError as e:
        raise HTTPException(422, str(e))
    finally:
        os.unlink(caminho)
