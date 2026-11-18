"""Mostra, nas MESMAS imagens do teste, o efeito de sombra, pouca luz, superexposição, desfoque e obstáculo.

Imagens do dataset com interferência SIMULADA: não são fotos reais. Servem como análise visual de
como cada interferência muda a probabilidade de fissura. Amostra: 3 positivas e 3 negativas que o
modelo acertou sem interferência (sorteio com semente fixa, não escolhidas a dedo).
Saída: evidencias/montagem_interferencias.png e interferencias_exemplos.csv
"""
import csv
import random

import matplotlib
import torch
from PIL import Image

import config
from dados import Fissuras, tf_base
from inferir import carregar_modelo
from teste_robustez import PERTURBACOES

matplotlib.use("Agg")
import matplotlib.pyplot as plt

USAR = ["original", "sombra", "pouca_luz", "superexposta", "desfoque", "obstaculo_central"]


def main():
    modelo = carregar_modelo()
    lim = config.LIMIAR_CONFIANCA
    itens = Fissuras("teste").itens

    def prob(img):
        with torch.no_grad():
            return torch.softmax(modelo(tf_base(img).unsqueeze(0)), 1)[0, 1].item()

    rnd = random.Random(config.SEMENTE)
    escolhidos = []
    for rot in (1, 0):
        cand = []
        for it in itens:
            if int(it["rotulo"]) == rot:
                img = Image.open(it["arquivo"]).convert("RGB")
                if int(prob(img) >= lim) == rot:
                    cand.append(it)
        escolhidos += rnd.sample(cand, 3)

    fig, eixos = plt.subplots(len(escolhidos), len(USAR), figsize=(2.6 * len(USAR), 2.9 * len(escolhidos)))
    linhas = []
    for i, it in enumerate(escolhidos):
        base = Image.open(it["arquivo"]).convert("RGB")
        real = int(it["rotulo"])
        nome = it["arquivo"].replace("\\", "/").split("/")[-1]
        for j, pert in enumerate(USAR):
            img = PERTURBACOES[pert](base)
            p = prob(img)
            ok = int(p >= lim) == real
            ax = eixos[i][j]
            ax.imshow(img)
            ax.axis("off")
            ax.set_title(f"{pert}\nP(fissura)={p:.2f} {'OK' if ok else 'ERRO'}", fontsize=7, color="green" if ok else "red")
            linhas.append({"arquivo": nome, "real": config.CLASSES[real], "perturbacao": pert, "p_fissura": round(p, 4), "acerto": ok})
        eixos[i][0].text(-0.05, 0.5, f"{nome}\nreal={config.CLASSES[real]}", transform=eixos[i][0].transAxes,
                         ha="right", va="center", fontsize=7)
    fig.tight_layout()
    fig.savefig(config.SAIDA / "montagem_interferencias.png", dpi=110, bbox_inches="tight")
    with open(config.SAIDA / "interferencias_exemplos.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(linhas[0]))
        w.writeheader()
        w.writerows(linhas)
    erros = [l for l in linhas if not l["acerto"]]
    print(f"{len(linhas)} casos, {len(erros)} erros")
    for e in erros:
        print(e)


if __name__ == "__main__":
    main()
