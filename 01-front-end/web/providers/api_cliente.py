"""Cliente HTTP da interface. Toda chamada à API passa por aqui e todo erro vira `ErroAPI` com texto simples.

Trata: API fora do ar, timeout, erro do servidor ou do LLM (5xx), entrada recusada (422) e resposta
que não é JSON. A interface nunca mostra stack trace ao cidadão.
"""
import os
import time

import requests
import streamlit as st

API_URL = os.getenv("API_URL", "http://localhost:8000")


class ErroAPI(Exception):
    def __init__(self, mensagem: str, codigo: int | None = None):
        super().__init__(mensagem)
        self.codigo = codigo


@st.cache_resource
def _sessao() -> requests.Session:
    """Uma conexão reaproveitada por processo (cache_resource: objeto não serializável)."""
    s = requests.Session()
    s.headers["User-Agent"] = "EloBairro-Web/1.0"
    return s


def _detalhe(r: requests.Response) -> str:
    try:
        d = r.json().get("detail", r.text)
    except ValueError:
        return r.text[:200]
    if isinstance(d, list):  # 422 da API: lista de {campo, mensagem}
        return "; ".join(f"{e.get('campo', '')}: {e.get('mensagem', '')}".strip(": ") for e in d)
    return str(d)


def chamar(metodo: str, caminho: str, timeout: float = 20, **kwargs) -> tuple[dict | list, float]:
    """Devolve (json, latência em ms)."""
    t0 = time.perf_counter()
    try:
        r = _sessao().request(metodo, f"{API_URL}{caminho}", timeout=timeout, **kwargs)
    except requests.ConnectionError:
        raise ErroAPI("Não foi possível falar com o sistema agora. Verifique a internet ou tente em instantes.")
    except requests.Timeout:
        raise ErroAPI("O sistema demorou demais para responder. Tente de novo.")
    ms = round((time.perf_counter() - t0) * 1000)
    if r.status_code == 422:
        raise ErroAPI(f"Confira o que foi preenchido: {_detalhe(r)}", 422)
    if r.status_code >= 500:
        raise ErroAPI(_detalhe(r) or "O sistema está com problema. Tente de novo em instantes.", r.status_code)
    if r.status_code >= 400:
        raise ErroAPI(_detalhe(r), r.status_code)
    try:
        return r.json(), ms
    except ValueError:
        raise ErroAPI("O sistema respondeu algo inesperado. Tente de novo.", r.status_code)


# --- leituras com cache curto (o painel não precisa bater na API a cada clique) ---

@st.cache_data(ttl=15, show_spinner=False)
def saude() -> dict:
    return chamar("GET", "/saude", timeout=4)[0]


@st.cache_data(ttl=20, show_spinner=False)
def protocolos(limite: int = 2000) -> list[dict]:
    return chamar("GET", "/protocolos", params={"limite": limite})[0]


@st.cache_data(ttl=5, show_spinner=False)
def eventos_som(limite: int = 50) -> list[dict]:
    return chamar("GET", "/iot/eventos", params={"limite": limite}, timeout=5)[0]


def limpar_cache() -> None:
    protocolos.clear()
    eventos_som.clear()


# --- ações ---

def perguntar(pergunta: str, historico: list[dict]):
    return chamar("POST", "/rag/perguntar", json={"pergunta": pergunta, "historico": historico[-6:]}, timeout=90)


def perguntar_por_voz(nome: str, dados: bytes, tipo: str):
    return chamar("POST", "/voz/perguntar", files={"arquivo": (nome, dados, tipo)}, timeout=180)


def falar(texto: str):
    return chamar("POST", "/voz/falar", json={"texto": texto[:1500]}, timeout=60)


def analisar_relato(texto: str, regiao: str, origem: str, foto: dict | None):
    corpo = {"texto": texto, "regiao": regiao, "origem": origem}
    if foto:
        corpo["foto"] = {k: foto[k] for k in ("probabilidade_fissura", "inspecao_recomendada")}
    return chamar("POST", "/relatos/analisar", json=corpo, timeout=40)


def confirmar_relato(corpo: dict):
    r = chamar("POST", "/relatos/confirmar", json=corpo, timeout=20)
    limpar_cache()
    return r


def mudar_status(protocolo: str, status: str):
    r = chamar("PATCH", f"/protocolos/{protocolo}/status", json={"status": status})
    limpar_cache()
    return r


def importar_rpa():
    r = chamar("POST", "/protocolos/importar-rpa", timeout=30)
    limpar_cache()
    return r


def enviar_evento_som(classe: str, confianca: float):
    r = chamar("POST", "/iot/eventos", json={"classe": classe, "confianca": confianca, "dispositivo": "simulador web"},
               headers={"X-Dispositivo-Token": os.getenv("IOT_TOKEN", "")})
    eventos_som.clear()
    return r
