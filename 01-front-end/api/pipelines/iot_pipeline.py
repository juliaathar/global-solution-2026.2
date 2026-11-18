"""Evento sonoro do OuviAí (pasta 05) vira alerta acessível para quem não ouve a porta.

Regras para reduzir falso positivo: a classe "ambiente" nunca alerta; campainha e batida só alertam
com confiança >= IOT_LIMIAR; e dois alertas da mesma classe em menos de 10 s contam como um só.
"""
from datetime import datetime

from api.core import config
from api.providers import repositorio
from api.schemas.iot import AlertaSom, EventoSom

MENSAGENS = {
    "campainha": ("🔔", "Tocaram a campainha"),
    "batida_porta": ("🚪", "Estão batendo na porta"),
    "ambiente": ("🔈", "Som do ambiente (sem alerta)"),
}
# Padrões de vibração (ms) para a evolução no celular: campainha = 2 longas; batida = 3 curtas
VIBRACAO = {"campainha": [600, 200, 600], "batida_porta": [200, 100, 200, 100, 200]}
JANELA_REPETICAO_S = 10


def _repetido(classe: str) -> bool:
    ultimos = repositorio.listar_eventos_som(limite=1, so_alertas=True)
    if not ultimos or ultimos[0]["classe"] != classe:
        return False
    delta = datetime.now() - datetime.fromisoformat(ultimos[0]["criado_em"])
    return delta.total_seconds() < JANELA_REPETICAO_S


def registrar(e: EventoSom) -> AlertaSom:
    if e.classe == "ambiente":
        alerta, motivo = False, "classe ambiente não gera alerta"
    elif e.confianca < config.IOT_LIMIAR:
        alerta, motivo = False, f"confiança abaixo do limiar ({config.IOT_LIMIAR:.0%})"
    elif _repetido(e.classe):
        alerta, motivo = False, f"repetição em menos de {JANELA_REPETICAO_S} s"
    else:
        alerta, motivo = True, "alerta emitido"
    salvo = repositorio.salvar_evento_som(e.classe, e.confianca, e.dispositivo, alerta, motivo)
    return montar(dict(salvo, classe=e.classe, confianca=e.confianca, dispositivo=e.dispositivo,
                       virou_alerta=alerta, motivo=motivo))


def montar(ev: dict) -> AlertaSom:
    icone, texto = MENSAGENS[ev["classe"]]
    return AlertaSom(id=ev["id"], classe=ev["classe"], confianca=ev["confianca"], dispositivo=ev["dispositivo"],
                     virou_alerta=ev["virou_alerta"], mensagem=texto, icone=icone, motivo=ev["motivo"],
                     criado_em=ev["criado_em"], limiar=config.IOT_LIMIAR,
                     vibracao_ms=VIBRACAO.get(ev["classe"]) if ev["virou_alerta"] else None)
