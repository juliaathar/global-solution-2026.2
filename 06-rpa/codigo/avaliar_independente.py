"""Mede o classificador na amostra escrita à mão, separando desenvolvimento (usada para melhorar as regras)
e teste (nunca olhada ao ajustar). Gera matriz de confusão e lista de erros por grupo.

Uso: python avaliar_independente.py [--erros]
"""
import csv
import sys
from collections import Counter

import config
from classificador import classificar

linhas = list(csv.DictReader(open(config.RAIZ / "dados_sinteticos" / "amostra_independente.csv", encoding="utf-8")))
mostrar_erros = "--erros" in sys.argv

for grupo in ("desenvolvimento", "teste", "todos"):
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
    if grupo != "todos" and (mostrar_erros or grupo == "teste"):
        for r, c, rev in erros:
            print(f"  ERRO {r['id']}: previsto {c['categoria']}/{c['urgencia']} (conf {c['confianca']}) "
                  f"real {r['categoria_real']}/{r['urgencia_real']}{' [revisão humana]' if rev else ''} | {r['texto'][:70]}")
    if grupo == "todos" and conf:
        print("Confusões de categoria (real -> previsto):", dict(conf))
