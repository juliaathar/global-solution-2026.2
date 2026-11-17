"""Classificador por regras (NLP simples). Devolve categoria, urgência e confiança.

Termos casam no início de palavra (\"esburacad\" pega esburacada e esburacado); um \"$\" no fim exige a palavra inteira.
Vocabulário ampliado a partir da análise de erros do grupo de desenvolvimento da amostra independente.
"""
import re

from deduplicacao import normalizar

CATEGORIAS = {
    "buraco": ["buraco", "asfalto", "cratera", "esburacad"],
    "iluminacao": ["poste", "iluminacao", "lampada", "apagado", "luminaria", "sem luz", "escuro", "escurid"],
    "lixo": ["lixo", "entulho", "cacamba", "sujeira", "sujo", "detrito"],
    "calcada": ["calcada", "rachadura", "cadeirante", "passeio"],
    "alagamento": ["alagamento", "bueiro", "enchente", "agua entra", "boca de lobo", "vira um rio"],
    "servico_saude": ["ubs$", "posto de saude", "unidade de saude", "consulta", "vacina", "medico", "remedio"],
}
URGENCIA_ALTA = ["acidente", "perigoso", "agua entrando", "alagamento", "risco", "ferido", "assalto"]
URGENCIA_PADRAO = {"lixo": "baixa", "alagamento": "alta"}  # alagamento ameaça casas e pessoas
SINAIS_PREVENTIVOS = ["nao escoa", "folhas"]  # entupimento sem água subindo: não é emergência


def _achou(texto: str, termo: str) -> bool:
    if termo.endswith("$"):
        return re.search(rf"\b{re.escape(termo[:-1])}\b", texto) is not None
    return re.search(rf"\b{re.escape(termo)}", texto) is not None


def classificar(texto: str) -> dict:
    t = normalizar(texto)
    pontos = {c: sum(_achou(t, p) for p in palavras) for c, palavras in CATEGORIAS.items()}
    melhor = max(pontos, key=pontos.get)
    total = sum(pontos.values())
    if pontos[melhor] == 0:
        return {"categoria": "indefinido", "urgencia": "baixa", "confianca": 0.0}
    confianca = round(pontos[melhor] / total, 2)
    if any(_achou(t, p) for p in URGENCIA_ALTA):
        urg = "alta"
    else:
        urg = URGENCIA_PADRAO.get(melhor, "media")
        if melhor == "alagamento" and any(_achou(t, p) for p in SINAIS_PREVENTIVOS):
            urg = "media"
    return {"categoria": melhor, "urgencia": urg, "confianca": confianca}
