"""Classificador por regras (NLP simples). Devolve categoria, urgência e confiança."""
from deduplicacao import normalizar

CATEGORIAS = {
    "buraco": ["buraco", "asfalto", "cratera"],
    "iluminacao": ["poste", "iluminacao", "lampada", "apagado"],
    "lixo": ["lixo", "entulho", "cacamba"],
    "calcada": ["calcada", "rachadura", "cadeirante"],
    "alagamento": ["alagamento", "bueiro", "enchente", "agua entrando"],
    "servico_saude": ["ubs", "posto de saude", "consulta", "vacina"],
}
URGENCIA_ALTA = ["acidente", "perigoso", "agua entrando", "alagamento", "risco", "ferido"]
URGENCIA_BAIXA = ["lixo", "entulho"]


def classificar(texto: str) -> dict:
    t = normalizar(texto)
    pontos = {c: sum(p in t for p in palavras) for c, palavras in CATEGORIAS.items()}
    melhor = max(pontos, key=pontos.get)
    total = sum(pontos.values())
    if pontos[melhor] == 0:
        return {"categoria": "indefinido", "urgencia": "baixa", "confianca": 0.0}
    confianca = round(pontos[melhor] / total, 2)
    if any(p in t for p in URGENCIA_ALTA):
        urg = "alta"
    elif any(p in t for p in URGENCIA_BAIXA):
        urg = "baixa"
    else:
        urg = "media"
    return {"categoria": melhor, "urgencia": urg, "confianca": confianca}
