"""Chunking do corpus. Três configurações comparáveis (ver CONFIGS).

Cada chunk preserva os metadados do documento (id, url, titulo, categoria, data_consulta) e
recebe o título no início do texto ("cabeçalho contextual"), porque muitas páginas têm
parágrafos curtos que sozinhos não dizem de que serviço falam.
"""
import json
import re
from pathlib import Path

CORPUS = Path(__file__).resolve().parents[2] / "corpus" / "documentos.jsonl"

CONFIGS = {
    "tam300_ov0":   {"metodo": "tamanho", "tamanho": 300, "overlap": 0},
    "tam800_ov120": {"metodo": "tamanho", "tamanho": 800, "overlap": 120},
    "secao":        {"metodo": "secao", "max": 1200},
}


def carregar_documentos(caminho: Path = CORPUS) -> list[dict]:
    with open(caminho, encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]


def _frases(texto: str) -> list[str]:
    """Divide em unidades que não cortam palavra: linhas e, se muito longas, frases."""
    unidades = []
    for linha in texto.split("\n"):
        linha = linha.strip()
        if not linha:
            continue
        if len(linha) > 400:
            unidades += [s.strip() for s in re.split(r"(?<=[.!?;])\s+", linha) if s.strip()]
        else:
            unidades.append(linha)
    return unidades


def _por_tamanho(texto: str, tamanho: int, overlap: int) -> list[str]:
    """Agrupa unidades até `tamanho` caracteres; o overlap repete o fim do chunk anterior."""
    partes, atual = [], ""
    for u in _frases(texto):
        if atual and len(atual) + len(u) + 1 > tamanho:
            partes.append(atual)
            cauda = atual[-overlap:] if overlap else ""
            cauda = cauda[cauda.find(" ") + 1:] if cauda else ""  # não começa no meio de palavra
            atual = (cauda + " " + u).strip()
        else:
            atual = (atual + "\n" + u).strip() if atual else u
    if atual:
        partes.append(atual)
    return partes


def _por_secao(texto: str, maximo: int) -> list[str]:
    """Cada título '## ...' abre uma seção; seções maiores que `maximo` são subdivididas."""
    secoes, atual = [], []
    for linha in texto.split("\n"):
        if linha.startswith("## ") and atual and not all(l.startswith("## ") for l in atual):
            secoes.append("\n".join(atual))
            atual = []
        atual.append(linha)
    if atual:
        secoes.append("\n".join(atual))
    saida = []
    for s in secoes:
        saida += [s] if len(s) <= maximo else _por_tamanho(s, maximo, 0)
    return saida


def chunkar(docs: list[dict], config: str) -> list[dict]:
    cfg = CONFIGS[config]
    chunks = []
    for d in docs:
        if cfg["metodo"] == "tamanho":
            partes = _por_tamanho(d["texto"], cfg["tamanho"], cfg["overlap"])
        else:
            partes = _por_secao(d["texto"], cfg["max"])
        for i, p in enumerate(partes):
            chunks.append({
                "chunk_id": f"{d['id']}#{i}",
                "doc_id": d["id"], "url": d["url"], "titulo": d["titulo"],
                "categoria": d["categoria"], "data_consulta": d["data_consulta"],
                "texto": f"{d['titulo']}\n{p.replace('## ', '')}",
            })
    return chunks


if __name__ == "__main__":
    docs = carregar_documentos()
    for nome in CONFIGS:
        c = chunkar(docs, nome)
        tam = [len(x["texto"]) for x in c]
        print(f"{nome:14s} chunks={len(c):4d} min={min(tam)} medio={sum(tam)//len(tam)} max={max(tam)}")
