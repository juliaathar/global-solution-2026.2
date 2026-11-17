"""Mede o acerto do classificador na amostra rotulada (lê o relatório da última execução)."""
import json

import config

dados = json.loads(config.RELATORIO.read_text(encoding="utf-8"))["protocolos"]
rotulados = [d for d in dados if d["categoria_real"] and d["categoria_real"] != "indefinido"]
n = len(rotulados)
cat = sum(d["categoria"] == d["categoria_real"] for d in rotulados)
urg = sum(d["urgencia"] == d["urgencia_real"] for d in rotulados)
print(f"Amostra: {n} relatos rotulados")
print(f"Acerto de categoria: {cat}/{n} = {cat / n:.1%}")
print(f"Acerto de urgência:  {urg}/{n} = {urg / n:.1%}")
erros = [d for d in rotulados if d["categoria"] != d["categoria_real"] or d["urgencia"] != d["urgencia_real"]]
for d in erros[:10]:
    print("ERRO", d["id"], d["categoria"], "!=", d["categoria_real"], "|", d["urgencia"], "!=", d["urgencia_real"])
