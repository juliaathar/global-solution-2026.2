"""Avaliação de chunking e recuperação (nível 1 do plano de testes).

Para cada configuração de chunking, mede nas perguntas com evidência esperada (R* e C*):
  - acerto de documento@k: algum trecho do top-k vem de um documento esperado
  - acerto de evidência@k: algum trecho do top-k, de documento esperado, contém a evidência marcada
  - MRR da evidência
Também mede, nas perguntas sem resposta (S*), quantas passariam pelo limiar de abstenção.

Uso (a partir de 03-generative-ai):  python avaliacao/avaliar_recuperacao.py
Saídas: evidencias/recuperacao_resumo.md e evidencias/recuperacao_detalhe.csv
"""
import csv
import json
import sys
import unicodedata
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from rag.chunking.chunking import CONFIGS, carregar_documentos, chunkar  # noqa: E402
from rag.motor import _consulta  # noqa: E402
from rag.retriever.bm25 import BM25  # noqa: E402

KS = (1, 3, 5)
LIMIARES = (0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.50)


def norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s.lower())
    return "".join(c for c in s if not unicodedata.combining(c))


def historico_de(p: dict) -> list[dict]:
    h = []
    for t in p.get("turnos_anteriores", []):
        h += [{"role": "user", "content": t["pergunta"]}, {"role": "assistant", "content": t["resposta"]}]
    return h


def validar_evidencias(perguntas, docs) -> None:
    por_id = {d["id"]: norm(d["texto"].replace("## ", "")) for d in docs}
    for p in perguntas:
        for d in p.get("docs_esperados", []):
            assert d in por_id, f"{p['id']}: documento inexistente {d}"
            if p.get("evidencia"):
                assert norm(p["evidencia"]) in por_id[d], f"{p['id']}: evidência não está em {d}"


def main() -> None:
    perguntas = json.load(open(Path(__file__).parent / "perguntas.json", encoding="utf-8"))
    docs = carregar_documentos()
    validar_evidencias(perguntas, docs)
    com_ev = [p for p in perguntas if p.get("evidencia")]
    sem_resp = [p for p in perguntas if p["tipo"] == "sem_resposta"]
    linhas, detalhe = [], []

    for nome in CONFIGS:
        bm25 = BM25(chunkar(docs, nome))
        doc_hit = {k: 0 for k in KS}
        ev_hit = {k: 0 for k in KS}
        rr = 0.0
        scores_ok = []
        for p in com_ev:
            res = bm25.buscar(_consulta(p["pergunta"], historico_de(p)), max(KS))
            esperados, ev = set(p["docs_esperados"]), norm(p["evidencia"])
            pos_ev = next((i for i, t in enumerate(res, 1) if t["doc_id"] in esperados and ev in norm(t["texto"])), None)
            pos_doc = next((i for i, t in enumerate(res, 1) if t["doc_id"] in esperados), None)
            for k in KS:
                doc_hit[k] += bool(pos_doc and pos_doc <= k)
                ev_hit[k] += bool(pos_ev and pos_ev <= k)
            rr += 1 / pos_ev if pos_ev else 0
            scores_ok.append(res[0]["score_rel"] if res else 0.0)
            detalhe.append({"config": nome, "id": p["id"], "pergunta": p["pergunta"], "pos_doc": pos_doc or "",
                            "pos_evidencia": pos_ev or "", "top1_doc": res[0]["doc_id"] if res else "",
                            "top1_score_rel": round(res[0]["score_rel"], 3) if res else 0,
                            "top1_trecho": (res[0]["texto"][:200].replace("\n", " | ") if res else "")})
        scores_sem = []
        for p in sem_resp:
            res = bm25.buscar(p["pergunta"], 1)
            scores_sem.append(res[0]["score_rel"] if res else 0.0)
            detalhe.append({"config": nome, "id": p["id"], "pergunta": p["pergunta"], "pos_doc": "", "pos_evidencia": "",
                            "top1_doc": res[0]["doc_id"] if res else "",
                            "top1_score_rel": round(scores_sem[-1], 3),
                            "top1_trecho": (res[0]["texto"][:200].replace("\n", " | ") if res else "")})
        n = len(com_ev)
        linhas.append({"config": nome, "chunks": len(bm25.chunks), "n": n,
                       **{f"doc@{k}": doc_hit[k] / n for k in KS}, **{f"ev@{k}": ev_hit[k] / n for k in KS},
                       "mrr": rr / n, "limiar": {
                           t: (sum(s < t for s in scores_ok) / n, sum(s >= t for s in scores_sem) / len(sem_resp))
                           for t in LIMIARES}})

    out = RAIZ / "evidencias"
    out.mkdir(exist_ok=True)
    with open(out / "recuperacao_detalhe.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(detalhe[0]))
        w.writeheader()
        w.writerows(detalhe)

    md = [f"# Avaliação de chunking e recuperação (BM25)\n",
          f"{len(com_ev)} perguntas com evidência esperada (R01-R17, C01-C04) e {len(sem_resp)} sem resposta (S01-S05).\n",
          "## Acerto por configuração de chunking\n",
          "| Config | Chunks | Doc@1 | Doc@3 | Doc@5 | Evid@1 | Evid@3 | Evid@5 | MRR |", "|---|---|---|---|---|---|---|---|---|"]
    for l in linhas:
        md.append(f"| {l['config']} | {l['chunks']} | " + " | ".join(f"{l[f'doc@{k}']:.2f}" for k in KS) + " | "
                  + " | ".join(f"{l[f'ev@{k}']:.2f}" for k in KS) + f" | {l['mrr']:.2f} |")
    md += ["\n## Limiar de abstenção (score relativo do melhor trecho)\n",
           "Falsa abstenção = pergunta respondível cujo melhor trecho fica abaixo do limiar. "
           "Falsa resposta = pergunta sem resposta cujo melhor trecho passa do limiar.\n"]
    for l in linhas:
        md += [f"**{l['config']}**\n", "| Limiar | Falsa abstenção (R+C) | Falsa resposta (S) |", "|---|---|---|"]
        md += [f"| {t:.2f} | {fa:.2f} | {fr:.2f} |" for t, (fa, fr) in l["limiar"].items()]
        md.append("")
    (out / "recuperacao_resumo.md").write_text("\n".join(md), encoding="utf-8")
    print("\n".join(md))


if __name__ == "__main__":
    main()
