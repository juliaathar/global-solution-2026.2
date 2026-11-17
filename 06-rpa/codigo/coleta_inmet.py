"""Avisos meteorológicos do Inmet (Alert-AS, feed RSS público).

XPath lê o XML do feed (`//item`); BeautifulSoup + CSS lê a tabela HTML dentro do CDATA do `description`.
Falha de rede, bloqueio ou XML inválido: usa o snapshot local, sem derrubar o robô.
"""
import logging
from datetime import datetime

from bs4 import BeautifulSoup
from lxml import etree

import config
from coleta_web import ErroColeta, baixar

log = logging.getLogger("rpa.inmet")


def _parse_data(txt: str):
    try:
        return datetime.strptime(txt.split(".")[0], "%Y-%m-%d %H:%M:%S")
    except (ValueError, AttributeError):
        return None


def extrair_avisos(xml: str) -> list[dict]:
    raiz = etree.fromstring(xml.encode("utf-8") if isinstance(xml, str) else xml)
    avisos = []
    for item in raiz.xpath("//item"):
        tabela = BeautifulSoup(item.findtext("description") or "", "lxml")
        campos = {th.get_text(strip=True): td.get_text(" ", strip=True)
                  for th in tabela.select("th") if (td := th.find_next_sibling("td"))}
        avisos.append({"id": (item.findtext("guid") or "").rsplit("/", 1)[-1],
                       "evento": campos.get("Evento", ""), "severidade": campos.get("Severidade", ""),
                       "inicio": _parse_data(campos.get("Início", "")), "fim": _parse_data(campos.get("Fim", "")),
                       "area": campos.get("Área", ""), "descricao": campos.get("Descrição", "")})
    return avisos


def filtrar_vigentes(avisos, agora=None, area=None, eventos=None):
    """Avisos da região (por nome da mesorregião), de eventos de chuva/vento, em vigor em `agora`."""
    agora = agora or datetime.now()
    area = area or config.INMET_AREA
    eventos = eventos or config.INMET_EVENTOS
    return [a for a in avisos
            if area.lower() in a["area"].lower() and a["evento"] in eventos
            and a["inicio"] and a["fim"] and a["inicio"] <= agora <= a["fim"]]


def coletar_avisos(agora=None) -> tuple[list[dict], str]:
    """Devolve (avisos vigentes para a região, origem 'web' ou 'snapshot'). Nunca levanta por falha de rede."""
    avisos, origem = [], "snapshot"
    if not config.OFFLINE:
        try:
            avisos, origem = extrair_avisos(baixar(config.INMET_URL)), "web"
            if not avisos:
                log.error("Feed do Inmet sem itens (formato mudou?); usando snapshot local")
                origem = "snapshot"
        except (ErroColeta, etree.XMLSyntaxError) as e:
            log.error("Feed do Inmet indisponível ou inválido (%s); usando snapshot local", e)
    if origem == "snapshot":
        avisos = extrair_avisos(config.INMET_SNAPSHOT.read_text(encoding="utf-8"))
    vigentes = filtrar_vigentes(avisos, agora)
    if origem == "snapshot":
        fins = [a["fim"] for a in avisos if a["fim"]]
        if not fins or max(fins) < (agora or datetime.now()):
            log.warning("Snapshot do Inmet desatualizado (avisos terminam em %s): sem alertas confiáveis até o feed voltar",
                        max(fins).strftime("%d/%m/%Y") if fins else "?")
    log.info("Inmet: %d avisos lidos, %d vigentes para %s (origem: %s)",
             len(avisos), len(vigentes), config.INMET_AREA, origem)
    return vigentes, origem
