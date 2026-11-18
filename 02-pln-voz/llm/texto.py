"""Palavras-chave de um texto, usadas pela base provisória e pela checagem de assunto."""
import re
import unicodedata

# Palavras que não indicam assunto. Sem elas, "sobre" (de "orienta sobre benefícios") casaria
# com qualquer pedido do tipo "escreva um poema sobre o mar".
VAZIAS = {
    "que", "com", "para", "por", "uma", "uns", "dos", "das", "nos", "nas", "mais", "como",
    "onde", "qual", "quais", "quem", "fica", "ficam", "tem", "ter", "ser", "sao", "foi",
    "meu", "minha", "seu", "sua", "isso", "essa", "esse", "aqui", "pelo", "pela",
    "sobre", "entre", "quando", "porque", "pode", "posso", "agora", "depois", "antes",
    "muito", "tambem", "ainda", "favor", "obrigado", "obrigada", "quero", "gostaria",
    "mas", "entao", "isto", "ela", "ele", "dela", "dele", "eu", "voce", "algum", "alguma",
}


def palavras(texto: str) -> set[str]:
    """Palavras com 3 letras ou mais, sem acento, minúsculas e sem as palavras vazias.
    Mantém siglas curtas como UBS e RG (RG tem 2 letras e fica de fora, UBS entra)."""
    t = unicodedata.normalize("NFD", texto.lower())
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    return {p for p in re.findall(r"\w+", t) if len(p) >= 3 and p not in VAZIAS}


def compartilham_radical(a: set[str], b: set[str], n: int = 3) -> bool:
    """True se alguma palavra de `a` começa com as mesmas `n` letras de uma de `b`
    ('levo' e 'leve', 'horas' e 'hora'). Aproximação simples de raiz comum."""
    return bool({x[:n] for x in a} & {y[:n] for y in b})
