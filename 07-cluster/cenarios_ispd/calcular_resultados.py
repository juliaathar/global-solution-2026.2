"""Calcula redução percentual, razão T2/T4, speedup e eficiência a partir dos tempos do iSPD.

Uso: python calcular_resultados.py T2 T4   (tempos em segundos, do Total Simulated Time)
"""
import sys


def calcular(t2: float, t4: float) -> dict:
    if t2 <= 0 or t4 <= 0:
        raise ValueError("Os tempos devem ser positivos.")
    return {
        "T2_s": t2,
        "T4_s": t4,
        "reducao_percentual": round((t2 - t4) / t2 * 100, 2),
        "razao_T2_T4": round(t2 / t4, 3),
        "speedup_ideal": 2.0,
        "eficiencia_percentual": round((t2 / t4) / 2 * 100, 1),
    }


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("Uso: python calcular_resultados.py T2 T4")
    for k, v in calcular(float(sys.argv[1]), float(sys.argv[2])).items():
        print(f"{k}: {v}")
