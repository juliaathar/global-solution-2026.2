"""Router do motor RAG. Monte no app principal com: app.include_router(rag.router)

O motor mora em 03-generative-ai/rag e é usado também pela voz (02). O LLM é chamado só aqui, no back-end.
"""
import sys
from pathlib import Path

from fastapi import APIRouter, HTTPException
from requests import RequestException

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "03-generative-ai"))

from rag.motor import responder  # noqa: E402

from ..schemas.rag import PerguntaRAG, RespostaRAG  # noqa: E402

router = APIRouter(prefix="/rag", tags=["rag"])


@router.post("/perguntar", response_model=RespostaRAG)
def perguntar(corpo: PerguntaRAG) -> RespostaRAG:
    historico = [t.model_dump() for t in corpo.historico]
    try:
        r = responder(corpo.pergunta.strip(), historico)
    except RequestException as e:  # LLM fora do ar, timeout ou chave inválida
        raise HTTPException(status_code=503, detail="O assistente está indisponível no momento. Tente de novo ou ligue 156.") from e
    return RespostaRAG(**{k: r[k] for k in ("resposta", "fontes", "abstencao", "bloqueada", "esclarecimento", "saida_bloqueada")})
