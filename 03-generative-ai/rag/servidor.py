"""Servidor mínimo para testar o motor RAG sozinho (a API completa fica em 01-front-end/api).

Uso (a partir da raiz do repositório):
    python 03-generative-ai/rag/servidor.py       # sobe em http://localhost:8000/docs
"""
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "01-front-end"))
sys.path.insert(0, str(RAIZ / "03-generative-ai"))

from fastapi import FastAPI  # noqa: E402

from api.routers import rag  # noqa: E402

app = FastAPI(title="EloBairro RAG (teste isolado)")
app.include_router(rag.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
