"""Compara os tempos simulados no iSPD com 2 e 4 workers.

Uso:
    python calcular_resultados.py T2 T4 [--workers-a 2] [--workers-b 4]

T2 e T4 são o Total Simulated Time (s) dos cenários A e B.
"""
import argparse
import sys


def calcular(t_a: float, t_b: float, n_a: int = 2, n_b: int = 4) -> dict:
    if t_a <= 0 or t_b <= 0:
        raise ValueError("Os tempos devem ser maiores que zero.")
    if n_b <= n_a:
        raise ValueError("O cenário B deve ter mais workers que o A.")
    razao = t_a / t_b
    ideal = n_b / n_a
    return {
        "reducao_pct": (t_a - t_b) / t_a * 100,
        "razao": razao,
        "speedup": razao,
        "ideal": ideal,
        "eficiencia_pct": razao / ideal * 100,
    }


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("t2", type=float, help="Total Simulated Time do cenário A (s)")
    p.add_argument("t4", type=float, help="Total Simulated Time do cenário B (s)")
    p.add_argument("--workers-a", type=int, default=2)
    p.add_argument("--workers-b", type=int, default=4)
    a = p.parse_args()
    try:
        r = calcular(a.t2, a.t4, a.workers_a, a.workers_b)
    except ValueError as e:
        print(f"Erro: {e}", file=sys.stderr)
        return 1

    print(f"| Métrica | Valor |")
    print(f"|---|---|")
    print(f"| T{a.workers_a} (s) | {a.t2:.2f} |")
    print(f"| T{a.workers_b} (s) | {a.t4:.2f} |")
    print(f"| Redução percentual do tempo | {r['reducao_pct']:.2f} % |")
    print(f"| Razão T{a.workers_a}/T{a.workers_b} | {r['razao']:.3f} |")
    print(f"| Speedup | {r['speedup']:.3f} (ideal {r['ideal']:.1f}) |")
    print(f"| Eficiência | {r['eficiencia_pct']:.1f} % |")
    if r["razao"] < r["ideal"]:
        print("\nGanho abaixo do ideal: investigar gargalo (rede, mestre, "
              "distribuição desigual ou escalonador).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
