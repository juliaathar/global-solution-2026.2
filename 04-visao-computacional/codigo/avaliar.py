"""Etapa 3: avalia no conjunto de TESTE (nunca visto no treino ou na validação).

Gera precisão, recall, F1, matriz de confusão e lista de erros para análise
(sombra, textura, iluminação, obstáculos).
"""
import csv

import matplotlib
import torch
from sklearn.metrics import ConfusionMatrixDisplay, classification_report, confusion_matrix
from torch.utils.data import DataLoader

import config
from dados import Fissuras
from treinar import criar_modelo

matplotlib.use("Agg")


def main():
    modelo = criar_modelo()
    modelo.load_state_dict(torch.load(config.MODELO, map_location="cpu"))
    modelo.eval()
    ds = Fissuras("teste")
    y_real, y_prev, confs = [], [], []
    with torch.no_grad():
        for x, y in DataLoader(ds, batch_size=config.BATCH):
            prob = torch.softmax(modelo(x), 1)
            conf, pred = prob.max(1)
            y_real += y.tolist()
            y_prev += pred.tolist()
            confs += conf.tolist()
    rel = classification_report(y_real, y_prev, target_names=config.CLASSES, digits=4)
    print(rel)
    (config.SAIDA / "relatorio_classificacao.txt").write_text(rel, encoding="utf-8")
    cm = confusion_matrix(y_real, y_prev)
    ConfusionMatrixDisplay(cm, display_labels=config.CLASSES).plot().figure_.savefig(config.SAIDA / "matriz_confusao.png", dpi=150)
    with open(config.SAIDA / "erros_teste.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["arquivo", "real", "previsto", "confianca"])
        for it, r, p, c in zip(ds.itens, y_real, y_prev, confs):
            if r != p:
                w.writerow([it["arquivo"], config.CLASSES[r], config.CLASSES[p], round(c, 3)])
    print("Amostra de teste:", len(y_real), "| erros:", sum(r != p for r, p in zip(y_real, y_prev)))


if __name__ == "__main__":
    main()
