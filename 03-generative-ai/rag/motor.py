"""Motor RAG do EloBairro: função única usada pela API (01) e pela voz (02).

    from rag.motor import responder
    r = responder("Onde fica a UBS do Jardim Satélite?", historico=[])
    r["resposta"], r["fontes"], r["abstencao"]
"""
from functools import lru_cache

from rag.chunking.chunking import carregar_documentos, chunkar
from rag.generator.generator import gerar
from rag.retriever.vetorial import Vetorial
from rag.seguranca import filtros

CONFIG_CHUNKING = "secao"   # escolhido em evidencias/retrievers_analise.md
MODELO_EMBEDDING = "e5large"
TOP_K = 3


@lru_cache(maxsize=4)
def indice(config: str = CONFIG_CHUNKING, modelo: str = MODELO_EMBEDDING) -> Vetorial:
    return Vetorial(chunkar(carregar_documentos(), config), modelo)


def _consulta(pergunta: str, historico: list[dict] | None) -> str:
    """Pergunta de continuação ("e o horário?") herda o assunto da última pergunta do usuário."""
    if historico and len(pergunta.split()) <= 5:
        ultimas = [m["content"] for m in historico if m["role"] == "user"]
        if ultimas:
            return f"{ultimas[-1]} {pergunta}"
    return pergunta


def responder(pergunta: str, historico: list[dict] | None = None,
              config: str = CONFIG_CHUNKING, k: int = TOP_K) -> dict:
    base = {"pergunta": pergunta, "trechos": [], "fontes": [], "abstencao": False, "bloqueada": False,
            "esclarecimento": False, "saida_bloqueada": ""}
    if filtros.pedido_malicioso(pergunta):
        return {**base, "resposta": filtros.MSG_RECUSA, "bloqueada": True}
    if filtros.pergunta_vaga(pergunta, bool(historico)):
        return {**base, "resposta": filtros.MSG_ESCLARECIMENTO, "esclarecimento": True}
    trechos = indice(config).buscar(_consulta(pergunta, historico), k)
    if filtros.evidencia_fraca(trechos):
        return {**base, "trechos": trechos, "resposta": filtros.MSG_ABSTENCAO, "abstencao": True}
    for t in trechos:
        t["texto"], t["neutralizado"] = filtros.neutralizar_contexto(t["texto"])
    resposta = gerar(pergunta, trechos, historico)
    motivo = filtros.resposta_suspeita(resposta, trechos)
    if motivo:
        return {**base, "trechos": trechos, "resposta": filtros.MSG_SAIDA_BLOQUEADA, "abstencao": True,
                "saida_bloqueada": motivo}
    fontes = [{"titulo": t["titulo"], "url": t["url"], "data_consulta": t["data_consulta"]} for t in trechos]
    return {**base, "trechos": trechos, "resposta": resposta, "fontes": fontes}
