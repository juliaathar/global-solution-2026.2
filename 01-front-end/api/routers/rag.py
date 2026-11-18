"""Router do motor RAG. Monte no app principal com: app.include_router(rag.router)

O motor mora em 03-generative-ai/rag e é usado também pela voz (02). O LLM é chamado só aqui, no back-end.
"""
import sys
from pathlib import Path

from fastapi import APIRouter, HTTPException
from requests import RequestException

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "03-generative-ai"))

from rag.motor import responder  # noqa: E402

from api.schemas.rag import PerguntaRAG, RespostaRAG  # noqa: E402

router = APIRouter(prefix="/rag", tags=["rag"])


@router.post("/perguntar", response_model=RespostaRAG)
def perguntar(corpo: PerguntaRAG) -> RespostaRAG:
    historico = [t.model_dump() for t in corpo.historico]
    try:
        r = responder(corpo.pergunta.strip(), historico)
    except RequestException as e:  # LLM fora do ar, timeout ou chave inválida
        raise HTTPException(status_code=503, detail="O assistente está indisponível no momento. Tente de novo ou ligue 156.") from e
    except (ImportError, OSError) as e:  # fastembed não instalado ou modelo de embedding não baixado
        raise HTTPException(status_code=503, detail="A busca nas fontes oficiais não está instalada neste servidor. "
                                                    "Ligue 156 para atendimento.") from e
    except (KeyError, ValueError) as e:  # resposta do LLM em formato inesperado
        raise HTTPException(status_code=502, detail="O assistente respondeu algo inesperado. Tente de novo.") from e
    return RespostaRAG(**{k: r[k] for k in ("resposta", "fontes", "abstencao", "bloqueada", "esclarecimento", "saida_bloqueada")})
