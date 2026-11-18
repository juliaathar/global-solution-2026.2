"""Retrievers vetorial (denso) e híbrido (BM25 + vetorial por Reciprocal Rank Fusion).

Embeddings via fastembed (ONNX, sem GPU). Os vetores dos chunks são guardados em cache
(rag/retriever/.cache) por modelo + conteúdo, então só são recalculados quando o chunking muda.
A pontuação vetorial é a similaridade de cosseno (vetores normalizados).
"""
import hashlib
from pathlib import Path

import numpy as np

from rag.retriever.bm25 import BM25

CACHE = Path(__file__).parent / ".cache"
MODELOS = {
    "minilm": "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",  # 384 dim, 128 tokens
    "e5large": "intfloat/multilingual-e5-large",                                # 1024 dim, 512 tokens
}
_modelos = {}


def _modelo(nome: str):
    if nome not in _modelos:
        from fastembed import TextEmbedding
        _modelos[nome] = TextEmbedding(MODELOS[nome])
    return _modelos[nome]


def _normalizar(m: np.ndarray) -> np.ndarray:
    return m / np.maximum(np.linalg.norm(m, axis=-1, keepdims=True), 1e-9)


class Vetorial:
    def __init__(self, chunks: list[dict], modelo: str = "minilm"):
        self.chunks, self.modelo = chunks, modelo
        chave = hashlib.sha1((modelo + "".join(c["texto"] for c in chunks)).encode()).hexdigest()[:16]
        arq = CACHE / f"{modelo}_{chave}.npy"
        if arq.exists():
            self.mat = np.load(arq)
        else:
            m = _modelo(modelo)
            textos = [c["texto"] for c in chunks]
            vet = m.passage_embed(textos) if modelo == "e5large" else m.embed(textos)
            self.mat = _normalizar(np.array(list(vet), dtype=np.float32))
            CACHE.mkdir(exist_ok=True)
            np.save(arq, self.mat)

    def _consulta(self, consulta: str) -> np.ndarray:
        m = _modelo(self.modelo)
        v = m.query_embed(consulta) if self.modelo == "e5large" else m.embed([consulta])
        return _normalizar(np.array(list(v), dtype=np.float32))[0]

    def similaridades(self, consulta: str) -> np.ndarray:
        return self.mat @ self._consulta(consulta)

    def buscar(self, consulta: str, k: int = 5) -> list[dict]:
        sims = self.similaridades(consulta)
        idx = np.argsort(-sims)[:k]
        return [{**self.chunks[i], "score": float(sims[i]), "score_rel": float(sims[i]), "cos": float(sims[i])} for i in idx]


class Hibrido:
    """RRF: score(chunk) = soma de 1/(k_rrf + posição) nos dois rankings. Mantém 'cos' e 'bm25_rel' para a abstenção."""

    def __init__(self, bm25: BM25, vet: Vetorial, k_rrf: int = 60, profundidade: int = 20):
        self.bm25, self.vet, self.k_rrf, self.prof = bm25, vet, k_rrf, profundidade

    def buscar(self, consulta: str, k: int = 5) -> list[dict]:
        sims = self.vet.similaridades(consulta)
        pos_den = np.argsort(-sims)[:self.prof]
        lex = self.bm25.buscar(consulta, self.prof)
        indice = {c["chunk_id"]: i for i, c in enumerate(self.vet.chunks)}
        fusao: dict[str, dict] = {}
        for pos, t in enumerate(lex, 1):
            e = fusao.setdefault(t["chunk_id"], {**t, "rrf": 0.0, "bm25_rel": t["score_rel"]})
            e["rrf"] += 1 / (self.k_rrf + pos)
        for pos, i in enumerate(pos_den, 1):
            e = fusao.setdefault(self.vet.chunks[i]["chunk_id"], {**self.vet.chunks[i], "rrf": 0.0, "bm25_rel": 0.0})
            e["rrf"] += 1 / (self.k_rrf + pos)
        topo = sorted(fusao.values(), key=lambda e: -e["rrf"])[:k]
        for e in topo:
            e["cos"] = float(sims[indice[e["chunk_id"]]])
            e["score"] = e["rrf"]
            e["score_rel"] = e["cos"]  # sinal de abstenção = cosseno do trecho
        return topo
