"""Fase 2: teste de robustez no conjunto de TESTE com perturbações sintéticas.

Simula interferências citadas no enunciado (sombra, pouca luz, desfoque, obstáculo, compressão).
É um proxy: NÃO substitui fotos reais de fachadas e calçadas. Saída: evidencias/robustez.csv
"""
import csv
import io

import torch
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter
from sklearn.metrics import f1_score, precision_score, recall_score

import config
from dados import Fissuras, tf_base
from inferir import carregar_modelo


def sombra(img):
    w, h = img.size
    m = Image.new("L", (w, h), 255)
    ImageDraw.Draw(m).polygon([(0, 0), (w * 0.7, 0), (w * 0.3, h), (0, h)], fill=110)
    m = m.filter(ImageFilter.GaussianBlur(12))
    return Image.composite(img, Image.new("RGB", (w, h), (0, 0, 0)), m)


def obstaculo(img):
    w, h = img.size
    out = img.copy()
    ImageDraw.Draw(out).rectangle([w * 0.35, h * 0.35, w * 0.65, h * 0.65], fill=(60, 90, 40))
    return out


def jpeg(img):
    b = io.BytesIO()
    img.save(b, "JPEG", quality=15)
    return Image.open(b).convert("RGB")


PERTURBACOES = {
    "original": lambda i: i,
    "sombra": sombra,
    "pouca_luz": lambda i: ImageEnhance.Brightness(i).enhance(0.4),
    "superexposta": lambda i: ImageEnhance.Brightness(i).enhance(1.8),
    "desfoque": lambda i: i.filter(ImageFilter.GaussianBlur(3)),
    "obstaculo_central": obstaculo,
    "jpeg_q15": jpeg,
    "baixa_resolucao": lambda i: i.resize((48, 48)).resize((227, 227)),
}


def main():
    modelo = carregar_modelo()
    itens = Fissuras("teste").itens
    imgs = [(Image.open(it["arquivo"]).convert("RGB"), int(it["rotulo"])) for it in itens]
    linhas = []
    for nome, f in PERTURBACOES.items():
        y, p = [], []
        for img, r in imgs:
            with torch.no_grad():
                prob = torch.softmax(modelo(tf_base(f(img)).unsqueeze(0)), 1)[0, 1].item()
            y.append(r)
            p.append(int(prob >= config.LIMIAR_CONFIANCA))
        linhas.append({"perturbacao": nome, "precisao": round(precision_score(y, p), 4),
                       "recall": round(recall_score(y, p), 4), "f1": round(f1_score(y, p), 4),
                       "acuracia": round(sum(a == b for a, b in zip(y, p)) / len(y), 4)})
        print(linhas[-1])
    with open(config.SAIDA / "robustez.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(linhas[0]))
        w.writeheader()
        w.writerows(linhas)


if __name__ == "__main__":
    main()
