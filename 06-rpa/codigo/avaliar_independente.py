"""Mede o classificador na amostra escrita à mão, separando desenvolvimento (usada para melhorar as regras)
e teste (nunca olhada ao ajustar). Gera matriz de confusão e lista de erros por grupo.

Uso: python avaliar_independente.py [--erros] [--amostra outro.csv]
Com --amostra, mede um CSV escrito por outra pessoa (colunas: id,texto,categoria_real,urgencia_real; coluna grupo opcional).
Sem a coluna grupo, tudo entra no grupo "externo". Veja dados_sinteticos/amostra_externa_modelo.csv.
"""
import csv
import sys
from collections import Counter

import config
from classificador import classificar

caminho = config.RAIZ / "dados_sinteticos" / "amostra_independente.csv"
if "--amostra" in sys.argv:
    caminho = sys.argv[sys.argv.index("--amostra") + 1]
linhas = list(csv.DictReader(open(caminho, encoding="utf-8")))
for r in linhas:
    r.setdefault("grupo", "") or None
    if not r["grupo"]:
        r["grupo"] = "externo"
mostrar_erros = "--erros" in sys.argv or "--amostra" in sys.argv
grupos = sorted({r["grupo"] for r in linhas}, key=lambda g: ("desenvolvimento", "teste").index(g) if g in ("desenvolvimento", "teste") else 9)

for grupo in (*grupos, "todos"):
    sub = [r for r in linhas if grupo == "todos" or r["grupo"] == grupo]
    cat = urg = revisao = 0
    erros, conf = [], Counter()
    for r in sub:
        c = classificar(r["texto"])
        ok_c, ok_u = c["categoria"] == r["categoria_real"], c["urgencia"] == r["urgencia_real"]
        cat += ok_c
        urg += ok_u
        rev = c["confianca"] < config.CONFIANCA_MINIMA
        revisao += rev
        if not ok_c:
            conf[(r["categoria_real"], c["categoria"])] += 1
        if not (ok_c and ok_u):
            erros.append((r, c, rev))
    n = len(sub)
    print(f"[{grupo}] {n} relatos | categoria {cat}/{n} = {cat / n:.1%} | urgência {urg}/{n} = {urg / n:.1%} | revisão humana {revisao}/{n}")
    if grupo != "todos" and mostrar_erros:
        for r, c, rev in erros:
            print(f"  ERRO {r['id']}: previsto {c['categoria']}/{c['urgencia']} (conf {c['confianca']}) "
                  f"real {r['categoria_real']}/{r['urgencia_real']}{' [revisão humana]' if rev else ''} | {r['texto'][:70]}")
    if grupo == "todos" and conf:
        print("Confusões de categoria (real -> previsto):", dict(conf))
