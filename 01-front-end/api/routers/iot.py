"""Eventos do OuviAí (pasta 05): a ponte do Edge Impulse manda a classe detectada; o app mostra o alerta."""
import hmac

from fastapi import APIRouter, Header, HTTPException, Query

from api.core import config
from api.pipelines import iot_pipeline
from api.providers import repositorio
from api.schemas.iot import AlertaSom, EventoSom

router = APIRouter(prefix="/iot", tags=["iot"])


@router.post("/eventos", response_model=AlertaSom, status_code=201)
def receber_evento(evento: EventoSom, x_dispositivo_token: str = Header(default="")):
    if config.IOT_TOKEN and not hmac.compare_digest(x_dispositivo_token, config.IOT_TOKEN):
        raise HTTPException(401, "Dispositivo não autorizado.")
    return iot_pipeline.registrar(evento)


@router.get("/eventos", response_model=list[AlertaSom])
def listar_eventos(limite: int = Query(50, ge=1, le=500), so_alertas: bool = False):
    return [iot_pipeline.montar(e) for e in repositorio.listar_eventos_som(limite, so_alertas)]
