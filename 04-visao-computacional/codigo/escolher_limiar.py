"""Escolhe o limiar de decisão na VALIDAÇÃO e só então mede no TESTE (sem contaminar o teste).

Critério definido antes de olhar os números, por ser triagem (perder fissura custa mais que
inspeção desnecessária): entre os limiares com recall >= 0,99 na validação, o de maior precisão
(empate: o maior limiar). Se nenhum atingir, usa o de maior recall.
Saída: evidencias/limiar_validacao.csv, evidencias/limiar_escolhido.json
"""
import csv
import json

import torch
from sklearn.metrics import confusion_matrix, f1_score, precision_score, recall_score
from torch.utils.data import DataLoader

import config
from dados import Fissuras
from treinar import criar_modelo

RECALL_ALVO = 0.99
LIMIARES = [round(0.05 * k, 2) for k in range(2, 19)]  # 0,10 a 0,90


def probabilidades(modelo, conjunto):
    y, p = [], []
    with torch.no_grad():
        for x, r in DataLoader(Fissuras(conjunto), batch_size=config.BATCH):
            p += torch.softmax(modelo(x), 1)[:, 1].tolist()
            y += r.tolist()
    return y, p


def metricas(y, p, lim):
    pred = [int(v >= lim) for v in p]
    tn, fp, fn, tp = confusion_matrix(y, pred).ravel()
    return {"limiar": lim, "precisao": round(precision_score(y, pred), 4), "recall": round(recall_score(y, pred), 4),
            "f1": round(f1_score(y, pred), 4), "fn": int(fn), "fp": int(fp)}


def main():
    modelo = criar_modelo()
    modelo.load_state_dict(torch.load(config.MODELO, map_location="cpu"))
    modelo.eval()
    yv, pv = probabilidades(modelo, "validacao")
    tabela = [metricas(yv, pv, l) for l in LIMIARES]
    with open(config.SAIDA / "limiar_validacao.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(tabela[0]))
        w.writeheader()
        w.writerows(tabela)
    for t in tabela:
        print("validacao", t)
    ok = [t for t in tabela if t["recall"] >= RECALL_ALVO]
    escolhido = max(ok, key=lambda t: (t["precisao"], t["limiar"])) if ok else max(tabela, key=lambda t: (t["recall"], t["limiar"]))
    yt, pt = probabilidades(modelo, "teste")
    no_teste = metricas(yt, pt, escolhido["limiar"])
    padrao_teste = metricas(yt, pt, 0.5)
    res = {"criterio": f"recall >= {RECALL_ALVO} na validação, maior precisão", "limiar_escolhido": escolhido["limiar"],
           "validacao": escolhido, "teste_no_limiar_escolhido": no_teste, "teste_no_limiar_0.5": padrao_teste}
    (config.SAIDA / "limiar_escolhido.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(res, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
