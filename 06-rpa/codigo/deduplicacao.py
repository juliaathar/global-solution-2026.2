import re
import unicodedata
from difflib import SequenceMatcher


def normalizar(texto: str) -> str:
    t = unicodedata.normalize("NFKD", texto.lower())
    t = "".join(c for c in t if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9 ]", "", t).strip()


def eh_duplicado(texto: str, vistos: list[str], limite: float) -> bool:
    n = normalizar(texto)
    return any(SequenceMatcher(None, n, v).ratio() >= limite for v in vistos)
