"""Valida a escolha (chunking por seção + vetorial e5-large) e o limiar de abstenção em perguntas NOVAS.

1. Calibra o limiar de cosseno no conjunto de desenvolvimento (perguntas.json).
2. Aplica esse limiar, sem reajustar, ao conjunto de validação (perguntas_validacao.json),
   escrito depois da calibração.
3. Mede a latência por consulta.

Uso (a partir de 03-generative-ai):  python avaliacao/validar_limiar.py
Saída: evidencias/validacao_limiar.md
"""
import json
import sys
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(Path(__file__).parent))

from avaliar_recuperacao import historico_de, norm, validar_evidencias  # noqa: E402
from avaliar_retrievers import SEM_EVIDENCIA, melhor_limiar  # noqa: E402
from rag.chunking.chunking import carregar_documentos, chunkar  # noqa: E402
from rag.motor import _consulta  # noqa: E402
from rag.retriever.bm25 import BM25  # noqa: E402
from rag.retriever.vetorial import Vetorial  # noqa: E402

AQUI = Path(__file__).parent


def rodar(ret, perguntas, sem_ids):
    """Devolve (sinais de respondíveis, sinais sem evidência, detalhes)."""
    ok, sem, det = [], [], []
    for p in perguntas:
        consulta = _consulta(p["pergunta"], historico_de(p))
        res = ret.buscar(consulta, 5)
        sinal = res[0]["score_rel"]
        if p.get("evidencia"):
            esp, ev = set(p["docs_esperados"]), norm(p["evidencia"])
            pos = next((i for i, t in enumerate(res, 1) if t["doc_id"] in esp and ev in norm(t["texto"])), None)
            ok.append(sinal)
            det.append((p["id"], p["pergunta"], pos, sinal, res[0]["doc_id"]))
        elif p["id"] in sem_ids:
            sem.append(sinal)
            det.append((p["id"], p["pergunta"], None, sinal, res[0]["doc_id"]))
    return ok, sem, det


def main() -> None:
    docs = carregar_documentos()
    dev = json.load(open(AQUI / "perguntas.json", encoding="utf-8"))
    val = json.load(open(AQUI / "perguntas_validacao.json", encoding="utf-8"))
    validar_evidencias(dev + val, docs)
    chunks = chunkar(docs, "secao")
    vet = Vetorial(chunks, "e5large")
    val_sem = {p["id"] for p in val if not p.get("evidencia")}

    ok_d, sem_d, _ = rodar(vet, dev, SEM_EVIDENCIA)
    limiar, fa_d, fr_d = melhor_limiar(ok_d, sem_d)
    # ponto médio entre o menor sinal respondível e o maior sem evidência, mais robusto que o valor de borda
    inferior_ok, superior_sem = min(ok_d), max(sem_d)
    limiar_medio = (inferior_ok + superior_sem) / 2 if inferior_ok > superior_sem else limiar

    ok_v, sem_v, det_v = rodar(vet, val, val_sem)
    n_ok, n_sem = len(ok_v), len(sem_v)
    ev1 = sum(1 for d in det_v if d[2] == 1)
    ev3 = sum(1 for d in det_v if d[2] and d[2] <= 3)

    t0 = time.perf_counter()
    for p in val:
        vet.buscar(p["pergunta"], 3)
    lat = (time.perf_counter() - t0) / len(val)

    def taxas(t):
        return sum(s < t for s in ok_v) / n_ok, sum(s >= t for s in sem_v) / n_sem

    md = ["# Validação do limiar (chunking por seção + e5-large)\n",
          f"Desenvolvimento: {len(ok_d)} respondíveis e {len(sem_d)} sem evidência. Validação (perguntas novas): {n_ok} respondíveis e {n_sem} sem evidência.\n",
          f"- Limiar de borda (máx. 1-FA-FR no desenvolvimento): **{limiar:.3f}** (FA {fa_d:.2f}, FR {fr_d:.2f})",
          f"- Menor sinal respondível no desenvolvimento: {inferior_ok:.3f}; maior sinal sem evidência: {superior_sem:.3f}",
          f"- Limiar do ponto médio da margem: **{limiar_medio:.3f}**\n",
          f"Recuperação na validação: evidência no top-1 em {ev1}/{sum(1 for d in det_v if d[2] is not None or d[0] in {p['id'] for p in val if p.get('evidencia')})}, "
          f"no top-3 em {ev3}.\n",
          "| Limiar | Falsa abstenção | Falsa resposta |", "|---|---|---|"]
    for nome, t in (("borda", limiar), ("ponto médio", limiar_medio)):
        fa, fr = taxas(t)
        md.append(f"| {t:.3f} ({nome}) | {fa:.2f} ({int(fa*n_ok)}/{n_ok}) | {fr:.2f} ({int(round(fr*n_sem))}/{n_sem}) |")
    md += ["\n## Detalhe da validação\n", "| Id | Pergunta | Pos. evidência | Cosseno top-1 | Documento top-1 |", "|---|---|---|---|---|"]
    md += [f"| {i} | {q} | {p if p else '-'} | {s:.3f} | {d} |" for i, q, p, s, d in det_v]
    md.append(f"\nLatência média por consulta (embedding da pergunta + busca, CPU): {lat*1000:.0f} ms.")
    (RAIZ / "evidencias" / "validacao_limiar.md").write_text("\n".join(md), encoding="utf-8")
    print("\n".join(md))


if __name__ == "__main__":
    main()
