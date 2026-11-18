"""Compara retrievers (BM25, vetorial, híbrido) em cada configuração de chunking.

Recuperação: acerto de evidência@k e MRR nas 21 perguntas com evidência (R*, C*).
Abstenção: o sinal do melhor trecho (score BM25 relativo ou cosseno) separa as 21 respondíveis das 9
perguntas sem evidência no corpus (S01-S05, A02, A03, D02, D03)? Mede-se AUC (sem limiar) e, para o
melhor limiar (índice de Youden), a falsa abstenção e a falsa resposta.

Uso (a partir de 03-generative-ai):  python avaliacao/avaliar_retrievers.py [--modelos minilm e5large]
Saídas: evidencias/retrievers_resumo.md e evidencias/retrievers_detalhe.csv
"""
import argparse
import csv
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(Path(__file__).parent))

from avaliar_recuperacao import historico_de, norm, validar_evidencias  # noqa: E402
from rag.chunking.chunking import CONFIGS, carregar_documentos, chunkar  # noqa: E402
from rag.motor import _consulta  # noqa: E402
from rag.retriever.bm25 import BM25  # noqa: E402
from rag.retriever.vetorial import Hibrido, Vetorial  # noqa: E402

KS = (1, 3, 5)
SEM_EVIDENCIA = {"S01", "S02", "S03", "S04", "S05", "A02", "A03", "D02", "D03"}


def auc(positivos: list[float], negativos: list[float]) -> float:
    """Probabilidade de um sinal de pergunta respondível superar o de uma sem evidência (Mann-Whitney)."""
    ganhos = sum((p > n) + 0.5 * (p == n) for p in positivos for n in negativos)
    return ganhos / (len(positivos) * len(negativos))


def melhor_limiar(pos: list[float], neg: list[float]) -> tuple[float, float, float]:
    """Limiar que maximiza (1 - falsa abstenção - falsa resposta). Devolve (limiar, falsa_abst, falsa_resp)."""
    melhor = (0.0, 1.0, 1.0)
    for t in sorted(set(pos + neg)):
        fa = sum(s < t for s in pos) / len(pos)
        fr = sum(s >= t for s in neg) / len(neg)
        if 1 - fa - fr > 1 - melhor[1] - melhor[2]:
            melhor = (t, fa, fr)
    return melhor


def main(modelos: list[str]) -> None:
    perguntas = json.load(open(Path(__file__).parent / "perguntas.json", encoding="utf-8"))
    docs = carregar_documentos()
    validar_evidencias(perguntas, docs)
    com_ev = [p for p in perguntas if p.get("evidencia")]
    sem_ev = [p for p in perguntas if p["id"] in SEM_EVIDENCIA]
    linhas, detalhe = [], []

    for cfg in CONFIGS:
        chunks = chunkar(docs, cfg)
        bm25 = BM25(chunks)
        retrievers = {"bm25": bm25}
        for m in modelos:
            vet = Vetorial(chunks, m)
            retrievers[f"vet_{m}"] = vet
            retrievers[f"hib_{m}"] = Hibrido(bm25, vet)
        for nome, r in retrievers.items():
            ev_hit, rr, sinal_ok = {k: 0 for k in KS}, 0.0, []
            for p in com_ev:
                res = r.buscar(_consulta(p["pergunta"], historico_de(p)), max(KS))
                esperados, ev = set(p["docs_esperados"]), norm(p["evidencia"])
                pos = next((i for i, t in enumerate(res, 1) if t["doc_id"] in esperados and ev in norm(t["texto"])), None)
                for k in KS:
                    ev_hit[k] += bool(pos and pos <= k)
                rr += 1 / pos if pos else 0
                sinal_ok.append(res[0]["score_rel"])
                detalhe.append({"config": cfg, "retriever": nome, "id": p["id"], "pos_evidencia": pos or "",
                                "top1_doc": res[0]["doc_id"], "sinal_top1": round(res[0]["score_rel"], 3)})
            sinal_sem = []
            for p in sem_ev:
                res = r.buscar(p["pergunta"], 1)
                sinal_sem.append(res[0]["score_rel"] if res else 0.0)
            t, fa, fr = melhor_limiar(sinal_ok, sinal_sem)
            n = len(com_ev)
            linhas.append({"config": cfg, "retriever": nome, **{f"ev@{k}": ev_hit[k] / n for k in KS},
                           "mrr": rr / n, "auc": auc(sinal_ok, sinal_sem), "limiar": t, "fa": fa, "fr": fr})
            print(f"{cfg:14s} {nome:14s} ev@1={ev_hit[1]/n:.2f} ev@3={ev_hit[3]/n:.2f} mrr={rr/n:.2f} auc={linhas[-1]['auc']:.2f}", flush=True)

    out = RAIZ / "evidencias"
    with open(out / "retrievers_detalhe.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(detalhe[0]))
        w.writeheader()
        w.writerows(detalhe)
    md = ["# Comparação de retrievers\n",
          f"{len(com_ev)} perguntas com evidência (R01-R17, C01-C04). Abstenção medida contra {len(sem_ev)} perguntas sem evidência "
          f"({', '.join(sorted(SEM_EVIDENCIA))}).\n",
          "AUC = chance de o sinal de uma pergunta respondível superar o de uma sem evidência (0,5 = acaso). "
          "Limiar, falsa abstenção (FA) e falsa resposta (FR) no ponto que maximiza 1 - FA - FR **neste mesmo conjunto** (otimista).\n",
          "| Chunking | Retriever | Evid@1 | Evid@3 | Evid@5 | MRR | AUC abstenção | Limiar | FA | FR |", "|---|---|---|---|---|---|---|---|---|---|"]
    for l in linhas:
        md.append(f"| {l['config']} | {l['retriever']} | {l['ev@1']:.2f} | {l['ev@3']:.2f} | {l['ev@5']:.2f} | {l['mrr']:.2f} | "
                  f"{l['auc']:.2f} | {l['limiar']:.2f} | {l['fa']:.2f} | {l['fr']:.2f} |")
    (out / "retrievers_resumo.md").write_text("\n".join(md), encoding="utf-8")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--modelos", nargs="+", default=["minilm", "e5large"])
    main(ap.parse_args().modelos)
