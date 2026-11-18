"""Relato de problema do bairro com confirmação humana antes de virar protocolo."""
from fastapi import APIRouter

from api.pipelines import relato_pipeline
from api.schemas.relato import ConfirmacaoRelato, PropostaRelato, ProtocoloCriado, RelatoEntrada

router = APIRouter(prefix="/relatos", tags=["relatos"])


@router.post("/analisar", response_model=PropostaRelato, summary="Proposta da IA (nada é gravado)")
def analisar(relato: RelatoEntrada) -> PropostaRelato:
    return relato_pipeline.analisar(relato)


@router.post("/confirmar", response_model=ProtocoloCriado, status_code=201,
             summary="Cidadão confirmou: gera o protocolo no banco do robô RPA")
def confirmar(confirmacao: ConfirmacaoRelato) -> ProtocoloCriado:
    return relato_pipeline.confirmar(confirmacao)
