"""API do EloBairro. Rodar a partir de 01-front-end: uvicorn api.main:app --port 8000

Dependências: fastapi, uvicorn e as do motor RAG (03-generative-ai/requirements.txt). O LLM é chamado só aqui,
no back-end; chaves ficam no .env da raiz (nunca versionado). CORS restrito a ALLOWED_ORIGINS.
"""
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routers import rag

app = FastAPI(title="EloBairro API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("ALLOWED_ORIGINS", "http://localhost:8501").split(","),
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
app.include_router(rag.router)


@app.get("/saude")
def saude():
    return {"status": "ok"}
