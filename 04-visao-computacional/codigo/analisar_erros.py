"""Fase 2: varredura de limiar no conjunto de TESTE e montagem visual dos erros.

Gera em evidencias/: varredura_limiar.csv e montagem_erros.png.
"""
import csv

import matplotlib
import torch
from PIL import Image
from sklearn.metrics import f1_score, precision_score, recall_score
from torch.utils.data import DataLoader

import config
from dados import Fissuras
from treinar import criar_modelo

matplotlib.use("Agg")
import matplotlib.pyplot as plt


def main():
    modelo = criar_modelo()
    modelo.load_state_dict(torch.load(config.MODELO, map_location="cpu"))
    modelo.eval()
    ds = Fissuras("teste")
    y, p = [], []
    with torch.no_grad():
        for x, r in DataLoader(ds, batch_size=config.BATCH):
            p += torch.softmax(modelo(x), 1)[:, 1].tolist()
            y += r.tolist()

    linhas = []
    for lim in (0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9):
        pred = [int(v >= lim) for v in p]
        fn = sum(1 for a, b in zip(y, pred) if a == 1 and b == 0)
        fp = sum(1 for a, b in zip(y, pred) if a == 0 and b == 1)
        linhas.append({"limiar": lim, "precisao": round(precision_score(y, pred), 4),
                       "recall": round(recall_score(y, pred), 4), "f1": round(f1_score(y, pred), 4),
                       "falsos_negativos": fn, "falsos_positivos": fp})
        print(linhas[-1])
    with open(config.SAIDA / "varredura_limiar.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(linhas[0]))
        w.writeheader()
        w.writerows(linhas)

    erros = [(it, r, v) for it, r, v in zip(ds.itens, y, p) if int(v >= config.LIMIAR_CONFIANCA) != r]
    cols = 4
    lin = (len(erros) + cols - 1) // cols
    fig, eixos = plt.subplots(lin, cols, figsize=(3.2 * cols, 3.4 * lin))
    for ax in eixos.flat:
        ax.axis("off")
    for ax, (it, r, v) in zip(eixos.flat, erros):
        ax.imshow(Image.open(it["arquivo"]).convert("RGB"))
        nome = it["arquivo"].replace("\\", "/").split("/")[-1]
        ax.set_title(f"{nome}\nreal={config.CLASSES[r]}\nP(fissura)={v:.2f}", fontsize=8)
    fig.tight_layout()
    fig.savefig(config.SAIDA / "montagem_erros.png", dpi=110)
    print("Erros:", len(erros))


if __name__ == "__main__":
    main()
