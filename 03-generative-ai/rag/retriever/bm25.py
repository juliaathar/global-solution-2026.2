"""Retriever lexical BM25 (implementação própria, sem dependências).

Normalização: minúsculas, sem acentos, tokens alfanuméricos, stopwords em português removidas.
Devolve chunks com a pontuação; a pontuação normalizada também alimenta a regra de abstenção.
"""
import math
import re
import unicodedata
from collections import Counter

STOP = set("""a o as os um uma uns umas de do da dos das em no na nos nas por para com sem sobre ao aos
e ou mas que se como quando onde qual quais quem eu voce meu minha seu sua ele ela eles elas isso isto
esse essa este esta ser estar ter ha foi sao era fica ficar posso pode precisa preciso quero queria
gostaria saber fazer ir vai la aqui mais muito pra pro""".split())


def tokenizar(texto: str) -> list[str]:
    t = unicodedata.normalize("NFKD", texto.lower())
    t = "".join(c for c in t if not unicodedata.combining(c))
    return [w for w in re.findall(r"[a-z0-9]+", t) if w not in STOP and len(w) > 1]


class BM25:
    def __init__(self, chunks: list[dict], k1: float = 1.5, b: float = 0.75):
        self.chunks, self.k1, self.b = chunks, k1, b
        self.tf = [Counter(tokenizar(c["texto"])) for c in chunks]
        self.len = [sum(t.values()) for t in self.tf]
        self.avg = sum(self.len) / max(len(self.len), 1)
        df = Counter(w for t in self.tf for w in t)
        n = len(chunks)
        self.idf = {w: math.log(1 + (n - f + 0.5) / (f + 0.5)) for w, f in df.items()}

    def _pontuar(self, termos: list[str], i: int) -> float:
        s, tf = 0.0, self.tf[i]
        for w in termos:
            f = tf.get(w, 0)
            if f:
                s += self.idf[w] * f * (self.k1 + 1) / (f + self.k1 * (1 - self.b + self.b * self.len[i] / self.avg))
        return s

    def buscar(self, consulta: str, k: int = 5) -> list[dict]:
        termos = tokenizar(consulta)
        if not termos:
            return []
        # teto teórico: cada termo da consulta casando perfeitamente (permite pontuação relativa 0..1)
        teto = sum(self.idf.get(w, 0) * (self.k1 + 1) for w in termos) or 1.0
        ranking = sorted(((self._pontuar(termos, i), i) for i in range(len(self.chunks))), reverse=True)[:k]
        return [{**self.chunks[i], "score": s, "score_rel": s / teto} for s, i in ranking if s > 0]
