import csv

import torch
from PIL import Image
from torch.utils.data import Dataset
from torchvision import transforms

import config

normaliza = transforms.Normalize(config.MEDIA, config.DESVIO)
tf_base = transforms.Compose([transforms.Resize((config.TAMANHO_IMG, config.TAMANHO_IMG)), transforms.ToTensor(), normaliza])
tf_treino = transforms.Compose([
    transforms.Resize((config.TAMANHO_IMG, config.TAMANHO_IMG)),
    transforms.RandomHorizontalFlip(), transforms.RandomVerticalFlip(),
    transforms.ColorJitter(brightness=0.3, contrast=0.3),
    transforms.ToTensor(), normaliza,
])


class Fissuras(Dataset):
    def __init__(self, conjunto):
        with open(config.MANIFESTO, encoding="utf-8") as f:
            self.itens = [l for l in csv.DictReader(f) if l["conjunto"] == conjunto]
        for it in self.itens:  # o manifesto guarda caminho relativo; aqui vira absoluto para abrir a imagem
            it["relativo"] = it["arquivo"]
            it["arquivo"] = str(config.IMAGENS / it["arquivo"])
        self.tf = tf_treino if conjunto == "treino" else tf_base

    def __len__(self):
        return len(self.itens)

    def __getitem__(self, i):
        it = self.itens[i]
        img = Image.open(it["arquivo"]).convert("RGB")
        return self.tf(img), torch.tensor(int(it["rotulo"]))
