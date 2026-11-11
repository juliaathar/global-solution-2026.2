"""Etapa 2: transferência de aprendizado com MobileNetV2 pré-treinada (ImageNet).

Justificativa: arquitetura leve, boa para CPU e para inferência em vídeo.
Congela o extrator de características e treina só a cabeça de classificação.
"""
import json
import time

import torch
from torch import nn
from torch.utils.data import DataLoader
from torchvision import models

import config
from dados import Fissuras


def criar_modelo():
    m = models.mobilenet_v2(weights=models.MobileNet_V2_Weights.DEFAULT)
    for p in m.features.parameters():
        p.requires_grad = False
    m.classifier[1] = nn.Linear(m.last_channel, 2)
    return m


def main():
    torch.manual_seed(config.SEMENTE)
    dispositivo = "cuda" if torch.cuda.is_available() else "cpu"
    modelo = criar_modelo().to(dispositivo)
    carga_tr = DataLoader(Fissuras("treino"), batch_size=config.BATCH, shuffle=True, num_workers=0)
    carga_va = DataLoader(Fissuras("validacao"), batch_size=config.BATCH, num_workers=0)
    otim = torch.optim.Adam(modelo.classifier.parameters(), lr=1e-3)
    perda = nn.CrossEntropyLoss()
    historico, melhor = [], 0.0
    for ep in range(1, config.EPOCAS + 1):
        t0 = time.time()
        modelo.train()
        soma = 0.0
        for x, y in carga_tr:
            x, y = x.to(dispositivo), y.to(dispositivo)
            otim.zero_grad()
            l = perda(modelo(x), y)
            l.backward()
            otim.step()
            soma += l.item() * len(y)
        modelo.eval()
        certos = total = 0
        with torch.no_grad():
            for x, y in carga_va:
                p = modelo(x.to(dispositivo)).argmax(1).cpu()
                certos += (p == y).sum().item()
                total += len(y)
        acc = certos / total
        historico.append({"epoca": ep, "perda_treino": soma / len(carga_tr.dataset), "acc_validacao": acc, "seg": round(time.time() - t0, 1)})
        print(historico[-1])
        if acc >= melhor:
            melhor = acc
            torch.save(modelo.state_dict(), config.MODELO)
    (config.SAIDA / "historico_treino.json").write_text(json.dumps(historico, indent=2), encoding="utf-8")
    print("Melhor acurácia de validação:", melhor, "| modelo salvo em", config.MODELO)


if __name__ == "__main__":
    main()
