"""Monta exemplos de ACERTOS do conjunto de teste (limiar de config.LIMIAR_CONFIANCA).

Mostra, para cada classe, os acertos de maior confiança e os acertos mais "apertados"
(perto do limiar), para contrastar com erros no relatório. Saída: evidencias/montagem_acertos.png
"""
import matplotlib
import torch
from PIL import Image
from torch.utils.data import DataLoader

import config
from dados import Fissuras
from treinar import criar_modelo

matplotlib.use("Agg")
import matplotlib.pyplot as plt

N = 4


def main():
    modelo = criar_modelo()
    modelo.load_state_dict(torch.load(config.MODELO, map_location="cpu"))
    modelo.eval()
    ds = Fissuras("teste")
    p = []
    with torch.no_grad():
        for x, _ in DataLoader(ds, batch_size=config.BATCH):
            p += torch.softmax(modelo(x), 1)[:, 1].tolist()
    lim = config.LIMIAR_CONFIANCA
    acertos = [(it, int(it["rotulo"]), v) for it, v in zip(ds.itens, p) if int(v >= lim) == int(it["rotulo"])]
    grupos = []
    for rot in (1, 0):
        cl = [a for a in acertos if a[1] == rot]
        conf = lambda a: a[2] if rot == 1 else 1 - a[2]
        cl.sort(key=conf)
        grupos.append((f"{config.CLASSES[rot]}: mais confiantes", cl[::-1][:N]))
        grupos.append((f"{config.CLASSES[rot]}: acertos apertados", cl[:N]))
    fig, eixos = plt.subplots(len(grupos), N, figsize=(3.2 * N, 3.5 * len(grupos)))
    for lin, (titulo, itens) in enumerate(grupos):
        for col in range(N):
            ax = eixos[lin][col]
            ax.axis("off")
            if col < len(itens):
                it, r, v = itens[col]
                ax.imshow(Image.open(it["arquivo"]).convert("RGB"))
                ax.set_title(f"{titulo}\n{it['arquivo'].replace(chr(92), '/').split('/')[-1]}  P(fissura)={v:.2f}", fontsize=7)
    fig.tight_layout()
    fig.savefig(config.SAIDA / "montagem_acertos.png", dpi=110)
    print("acertos:", len(acertos), "limiar:", lim)


if __name__ == "__main__":
    main()
