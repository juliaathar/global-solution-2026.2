"""API do EloBairro: ponto único de integração das disciplinas.

Rodar a partir de 01-front-end:  uvicorn api.main:app --port 8000      (documentação em /docs)

| Rota            | Disciplina que ela chama                                   |
|-----------------|------------------------------------------------------------|
| /rag            | 03 Generative AI (motor RAG)                               |
| /voz            | 02 PLN (STT, adaptação para fala, TTS) + 03                |
| /visao          | 04 Visão Computacional (fissuras em foto e vídeo)          |
| /relatos        | 06 RPA (máscara, classificador, banco de protocolos) + LLM |
| /protocolos     | 06 RPA (contrato POST /protocolos do robô) e painel        |
| /iot            | 05 IoT (eventos do OuviAí / Edge Impulse)                  |

O LLM é chamado só aqui, no back-end. Chaves ficam no .env da raiz (nunca versionado).
CORS restrito a ALLOWED_ORIGINS. Um módulo pesado que não esteja instalado (torch, fastembed)
desliga só a sua rota; o resto da API continua no ar.
"""
import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api.core import config
from api.routers import iot, painel, protocolos, relatos, voz

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("elobairro.api")

app = FastAPI(title="EloBairro API", version="1.0",
              description="Serviços públicos do bairro por voz, texto e foto. Projeto FIAP Global Solution 2026.2.")
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.ALLOWED_ORIGINS,
    allow_methods=["GET", "POST", "PATCH"],
    allow_headers=["Content-Type", "X-Dispositivo-Token"],
)

MODULOS: dict[str, str] = {}
for nome, rota in (("relatos", relatos), ("protocolos", protocolos), ("iot", iot), ("painel", painel), ("voz", voz)):
    app.include_router(rota.router)
    MODULOS[nome] = "ok"

for nome in ("rag", "visao"):  # dependem de bibliotecas pesadas das pastas 03 e 04
    try:
        modulo = __import__(f"api.routers.{nome}", fromlist=["router"])
        app.include_router(modulo.router)
        MODULOS[nome] = "ok"
    except Exception as e:  # ImportError, modelo ausente etc.
        MODULOS[nome] = f"indisponível ({e.__class__.__name__})"
        log.warning("Módulo %s desligado: %s", nome, e)


MENSAGENS_422 = {
    "missing": "campo obrigatório",
    "string_too_short": "texto curto demais (mínimo {min_length} caracteres)",
    "string_too_long": "texto longo demais (máximo {max_length} caracteres)",
    "literal_error": "valor não permitido",
    "greater_than_equal": "valor menor que o permitido",
    "less_than_equal": "valor maior que o permitido",
    "string_pattern_mismatch": "formato inválido",
}


@app.exception_handler(RequestValidationError)
async def entrada_invalida(request: Request, exc: RequestValidationError):
    """422 em português, com o campo e o motivo, para a interface mostrar ao cidadão."""
    erros = []
    for e in exc.errors():
        modelo = MENSAGENS_422.get(e["type"])
        msg = modelo.format(**e.get("ctx", {})) if modelo else str(e.get("msg", "valor inválido"))
        msg = msg.removeprefix("Value error, ")
        erros.append({"campo": ".".join(str(p) for p in e["loc"] if p != "body"), "mensagem": msg})
    return JSONResponse(status_code=422, content={"detail": erros})


@app.exception_handler(Exception)
async def erro_inesperado(request: Request, exc: Exception):
    log.exception("Erro inesperado em %s", request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Erro interno. Tente de novo em instantes."})


@app.get("/saude", tags=["saude"])
def saude():
    return {"status": "ok", "modulos": MODULOS,
            "llm": config.LLM_PROVIDER if config.LLM_PROVIDER != "extrativo" else "sem LLM (regras)"}
