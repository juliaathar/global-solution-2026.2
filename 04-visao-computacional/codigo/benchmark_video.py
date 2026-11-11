"""Etapa 5: processa um vídeo curto (ou pasta de imagens) e mede latência média e FPS.

Uso: python benchmark_video.py caminho/video.mp4
     python benchmark_video.py pasta_com_imagens/
Registre no relatório: equipamento, resolução e resultados impressos.
"""
import platform
import statistics
import sys
import time
from pathlib import Path

import cv2
from PIL import Image

import config
from inferir import carregar_modelo, predizer


def quadros(origem: Path):
    if origem.is_dir():
        for p in sorted(origem.iterdir()):
            if p.suffix.lower() in {".jpg", ".jpeg", ".png"}:
                yield Image.open(p)
        return
    cap = cv2.VideoCapture(str(origem))
    while True:
        ok, q = cap.read()
        if not ok:
            break
        yield Image.fromarray(cv2.cvtColor(q, cv2.COLOR_BGR2RGB))
    cap.release()


def main():
    origem = Path(sys.argv[1])
    carregar_modelo()  # aquecimento fora da medição
    tempos, alertas, res = [], 0, None
    t_total = time.perf_counter()
    for img in quadros(origem):
        res = res or img.size
        t0 = time.perf_counter()
        r = predizer(img)
        tempos.append(time.perf_counter() - t0)
        alertas += r["inspecao_recomendada"]
    total = time.perf_counter() - t_total
    if not tempos:
        raise SystemExit("Nenhum quadro processado. Verifique o caminho.")
    print(f"Equipamento: {platform.processor() or platform.machine()} | {platform.platform()}")
    print(f"Resolução dos quadros: {res[0]}x{res[1]} (redimensionado para {config.TAMANHO_IMG}x{config.TAMANHO_IMG})")
    print(f"Quadros: {len(tempos)} | alertas de inspeção: {alertas}")
    print(f"Latência média: {statistics.mean(tempos) * 1000:.1f} ms | mediana: {statistics.median(tempos) * 1000:.1f} ms")
    print(f"FPS (fim a fim): {len(tempos) / total:.1f}")


if __name__ == "__main__":
    main()
