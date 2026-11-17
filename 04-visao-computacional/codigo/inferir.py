"""Etapa 4: função de inferência usada pela API do app (01-front-end/api).

predizer(imagem) devolve rótulo, confiança e se há necessidade de inspeção.
Aviso: fissura na imagem não define gravidade nem segurança estrutural; serve para triagem.
"""
from functools import lru_cache

import torch
from PIL import Image

import config
from dados import tf_base
from treinar import criar_modelo

AVISO = "Triagem apenas. A imagem não permite avaliar a gravidade nem a segurança da estrutura."


@lru_cache(maxsize=1)
def carregar_modelo():
    m = criar_modelo()
    m.load_state_dict(torch.load(config.MODELO, map_location="cpu"))
    return m.eval()


def predizer(imagem: Image.Image, limiar: float = config.LIMIAR_CONFIANCA) -> dict:
    x = tf_base(imagem.convert("RGB")).unsqueeze(0)
    with torch.no_grad():
        prob = torch.softmax(carregar_modelo()(x), 1)[0]
    p_fissura = float(prob[1])
    return {
        "rotulo": config.CLASSES[1] if p_fissura >= limiar else config.CLASSES[0],
        "confianca": round(max(p_fissura, 1 - p_fissura), 4),
        "probabilidade_fissura": round(p_fissura, 4),
        "inspecao_recomendada": p_fissura >= limiar,
        "aviso": AVISO,
    }


if __name__ == "__main__":
    import sys
    print(predizer(Image.open(sys.argv[1])))
