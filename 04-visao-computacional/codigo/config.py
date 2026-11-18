"""Configuração do módulo de Visão Computacional (classificação de fissuras).

Base: Concrete Crack Images for Classification (Mendeley, 40 mil imagens 227x227).
Baixe e extraia para 04-visao-computacional/imagens/ com as pastas:
    imagens/Positive/  (com fissura)
    imagens/Negative/  (sem fissura)
"""
import os
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
IMAGENS = Path(os.getenv("VC_IMAGENS", RAIZ / "imagens"))
SAIDA = RAIZ / "evidencias"
MANIFESTO = SAIDA / "manifesto_split.csv"
MODELO = Path(os.getenv("VC_MODELO", RAIZ / "codigo" / "modelo_fissuras.pt"))

CLASSES = ["sem_fissura", "com_fissura"]   # índice 0 e 1
PASTAS = {"Negative": 0, "Positive": 1}

AMOSTRA_POR_CLASSE = int(os.getenv("VC_AMOSTRA", "2000"))
TAMANHO_BLOCO = 100            # arquivos consecutivos tratados como mesma origem
PROPORCOES = (0.7, 0.15, 0.15)  # treino, validação, teste
SEMENTE = 42

TAMANHO_IMG = 224
MEDIA = (0.485, 0.456, 0.406)
DESVIO = (0.229, 0.224, 0.225)
EPOCAS = int(os.getenv("VC_EPOCAS", "5"))
BATCH = 32
# 0,45: escolhido na VALIDAÇÃO (recall >= 0,99 com maior precisão); ver evidencias/limiar_escolhido.json
LIMIAR_CONFIANCA = float(os.getenv("VC_LIMIAR", "0.45"))
