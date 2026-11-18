"""Provider do módulo de Visão Computacional: liga a API ao código de 04-visao-computacional."""
import sys
import time
from pathlib import Path

import cv2
from PIL import Image

CODIGO_VC = Path(__file__).resolve().parents[3] / "04-visao-computacional" / "codigo"
if str(CODIGO_VC) not in sys.path:
    sys.path.insert(0, str(CODIGO_VC))

import config as vc_config  # noqa: E402
import inferir  # noqa: E402


class ModeloIndisponivel(RuntimeError):
    pass


def limiar_padrao() -> float:
    return vc_config.LIMIAR_CONFIANCA


def carregar():
    if not Path(vc_config.MODELO).exists():
        raise ModeloIndisponivel("Modelo não encontrado. Rode treinar.py em 04-visao-computacional/codigo.")
    return inferir.carregar_modelo()


def classificar_imagem(img: Image.Image, limiar: float) -> dict:
    carregar()
    t0 = time.perf_counter()
    r = inferir.predizer(img, limiar)
    r["limiar"] = limiar
    r["latencia_ms"] = round((time.perf_counter() - t0) * 1000, 1)
    return r


def classificar_video(caminho: str, passo: int, limiar: float, max_quadros: int) -> dict:
    carregar()
    cap = cv2.VideoCapture(caminho)
    if not cap.isOpened():
        raise ValueError("Não foi possível abrir o vídeo.")
    fps_video = cap.get(cv2.CAP_PROP_FPS) or 25.0
    quadros, tempos, i, res = [], [], 0, None
    t_total = time.perf_counter()
    while len(quadros) < max_quadros:
        ok, q = cap.read()
        if not ok:
            break
        if i % passo == 0:
            img = Image.fromarray(cv2.cvtColor(q, cv2.COLOR_BGR2RGB))
            res = res or img.size
            t0 = time.perf_counter()
            r = inferir.predizer(img, limiar)
            tempos.append(time.perf_counter() - t0)
            quadros.append({"indice": i, "tempo_s": round(i / fps_video, 2),
                            "probabilidade_fissura": r["probabilidade_fissura"],
                            "alerta": r["inspecao_recomendada"]})
        i += 1
    cap.release()
    if not quadros:
        raise ValueError("Nenhum quadro pôde ser lido do vídeo.")
    total = time.perf_counter() - t_total
    alertas = sum(q["alerta"] for q in quadros)
    return {
        "quadros_analisados": len(quadros),
        "quadros_com_alerta": alertas,
        "percentual_alertas": round(100 * alertas / len(quadros), 1),
        "latencia_media_ms": round(1000 * sum(tempos) / len(tempos), 1),
        "fps_processamento": round(len(quadros) / total, 1),
        "resolucao_original": f"{res[0]}x{res[1]}",
        "passo_amostragem": passo,
        "limiar": limiar,
        "aviso": inferir.AVISO,
        "quadros": quadros,
    }
