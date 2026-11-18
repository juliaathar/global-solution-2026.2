"""Protocolos: recebe os do robô RPA (contrato de 06-rpa/codigo/api_simulada.py) e lista para o gestor."""
import json
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from api.providers import repositorio, rpa_provider
from api.schemas.protocolo import AtualizarStatus, Ocorrencia, ProtocoloRobo, ResultadoImportacao

router = APIRouter(prefix="/protocolos", tags=["protocolos"])


@router.post("", status_code=201, summary="Notificação do robô RPA (POST /protocolos)")
async def receber_do_robo(request: Request):
    """Contrato do robô: 201 {"recebido": ...}; 400 se o corpo não for JSON ou faltar "protocolo"."""
    try:
        corpo = ProtocoloRobo(**json.loads(await request.body() or b""))
    except (json.JSONDecodeError, UnicodeDecodeError, TypeError, ValidationError):
        return JSONResponse(status_code=400, content={"erro": "envie JSON com o campo 'protocolo'"})
    dados = corpo.model_dump()
    novo = repositorio.salvar_ocorrencia(
        protocolo=corpo.protocolo, origem="robo_rpa", canal="robo", categoria=corpo.categoria or "indefinido",
        urgencia=corpo.urgencia or "media", confianca=corpo.confianca, regiao="Não informada", status="aberto",
        metodo="regras", resumo=corpo.encaminhamento or "", alerta_inmet=corpo.alerta_inmet or "")
    if not novo:
        repositorio.completar_ocorrencia(corpo.protocolo, **{k: v for k, v in dados.items() if k != "protocolo"})
    return {"recebido": corpo.protocolo}


@router.get("", response_model=list[Ocorrencia], summary="Lista para o painel, com filtros")
def listar(categoria: Optional[str] = Query(None, max_length=20), urgencia: Optional[str] = Query(None, max_length=10),
           regiao: Optional[str] = Query(None, max_length=20), origem: Optional[str] = Query(None, max_length=10),
           status: Optional[str] = Query(None, max_length=12), limite: int = Query(500, ge=1, le=2000)):
    return repositorio.listar_ocorrencias(categoria, urgencia, regiao, origem, status, limite)


@router.patch("/{protocolo}/status", response_model=dict, summary="Gestor muda o status (revisão humana)")
def mudar_status(protocolo: str, corpo: AtualizarStatus):
    if not repositorio.atualizar_status(protocolo, corpo.status):
        raise HTTPException(404, "Protocolo não encontrado.")
    return {"protocolo": protocolo, "status": corpo.status}


@router.post("/importar-rpa", response_model=ResultadoImportacao,
             summary="Carrega no painel o último relatório de execução do robô RPA")
def importar_rpa():
    arquivo, dados = rpa_provider.relatorio_execucao()
    if not arquivo:
        raise HTTPException(404, "Nenhum relatório do robô encontrado. Rode 06-rpa/codigo/main.py.")
    novos = existentes = 0
    for p in dados.get("protocolos", []):
        ok = repositorio.salvar_ocorrencia(
            protocolo=p["protocolo"], origem="robo_rpa", canal="robo", categoria=p.get("categoria", "indefinido"),
            urgencia=p.get("urgencia", "media"), confianca=p.get("confianca"), regiao="Não informada",
            status="aberto", metodo="regras", resumo=p.get("encaminhamento", ""),
            alerta_inmet=p.get("alerta_inmet", ""))
        novos += ok
        existentes += not ok
    return ResultadoImportacao(arquivo=arquivo.name, importados=novos, ja_existiam=existentes)
