"""Avaliação do TTS por NOTA GERAL, dada por duplas de avaliadores, em escala de 1 a 10 e convertida para 1 a 5.

    python testes/tts_notas_gerais.py --importar "10 7 10 ..."   # 60 números: 3 por áudio, na ordem aval_01 ... aval_20
    python testes/tts_notas_gerais.py                            # converte, junta com a chave cega e gera o resumo

Contexto: o grupo avaliou os 20 áudios do `tts_cego.py` com 6 pessoas (os 3 integrantes e um familiar de cada um) em
3 duplas. Cada dupla deu UMA nota geral por áudio (média da dupla, arredondada), de 1 a 10. Não há notas separadas de
naturalidade e de clareza, e isso é uma limitação: o enunciado pede as duas. O enunciado também pede a escala de 1 a 5,
então a nota é convertida por `nota_1a5 = 1 + (nota - 1) * 4 / 9`, que preserva os extremos (1 vira 1 e 10 vira 5).
A conversão é uma suposição de equivalência entre as escalas.

Entradas: testes/tts_cego_notas_gerais.csv (aval, dupla, nota_1a10), testes/tts_cego_chave.csv (aval -> motor, id) e
evidencias/tts_tempos.csv. Saídas: evidencias/tts_notas.csv e evidencias/tts_resumo.md.
"""
import argparse
import statistics as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from util import EVIDENCIAS, TESTES, escrever_csv, fmt, ler_csv, tabela_md  # noqa: E402

NOTAS = TESTES / "tts_cego_notas_gerais.csv"
CHAVE = TESTES / "tts_cego_chave.csv"
N_AUDIOS, N_DUPLAS = 20, 3


def converter(nota: int) -> float:
    """1 a 10 -> 1 a 5, preservando os extremos."""
    return 1 + (nota - 1) * 4 / 9


def importar(sequencia: str, n_audios: int = N_AUDIOS, n_duplas: int = N_DUPLAS) -> list[dict]:
    """Transforma os números (3 por áudio, na ordem aval_01 ... aval_20) em linhas aval, dupla, nota_1a10."""
    try:
        nums = [int(x) for x in sequencia.split()]
    except ValueError:
        raise ValueError("todos os valores precisam ser inteiros")
    if len(nums) != n_audios * n_duplas:
        raise ValueError(f"esperados {n_audios * n_duplas} números ({n_duplas} por áudio), vieram {len(nums)}")
    fora = [n for n in nums if not 1 <= n <= 10]
    if fora:
        raise ValueError(f"notas fora da escala de 1 a 10: {sorted(set(fora))}")
    return [{"aval": f"aval_{a + 1:02d}", "dupla": d + 1, "nota_1a10": nums[a * n_duplas + d]}
            for a in range(n_audios) for d in range(n_duplas)]


def consolidar(notas: list[dict], chave: list[dict]) -> list[dict]:
    por_aval = {k["aval"]: k for k in chave}
    saida = []
    for n in notas:
        k = por_aval[n["aval"]]
        v = int(n["nota_1a10"])
        saida.append({"aval": n["aval"], "motor": k["motor"], "id": k["id"], "arquivo": k["arquivo"],
                      "dupla": n["dupla"], "nota_1a10": v, "nota_1a5": round(converter(v), 3)})
    return saida


def resumir(linhas: list[dict], tempos: list[dict] | None = None) -> str:
    motores = list(dict.fromkeys(r["motor"] for r in linhas))
    corpo = []
    for m in motores:
        v = [float(r["nota_1a5"]) for r in linhas if r["motor"] == m]
        sint = [float(t["sintese_s"]) for t in (tempos or []) if t["motor"] == m]
        corpo.append([m, len({r["aval"] for r in linhas if r["motor"] == m}), len(v), fmt(st.fmean(v), 2),
                      fmt(st.stdev(v), 2) if len(v) > 1 else "n/d", fmt(min(v), 2), fmt(max(v), 2),
                      fmt(st.fmean(sint), 2) if sint else "n/d"])
    out = ["# TTS: nota geral dada por 6 avaliadores em 3 duplas\n",
           "Cada dupla (um integrante do grupo e um familiar) deu uma nota geral a cada áudio, em escala de 1 a 10, "
           "convertida para 1 a 5 por `1 + (nota - 1) * 4 / 9`. **Naturalidade e clareza não foram avaliadas "
           "separadamente.** A avaliação foi cega (áudios embaralhados, com nomes neutros e mesmo formato).\n",
           tabela_md(["Motor", "Áudios", "Notas", "Nota geral média (1-5)", "Desvio padrão", "Mínima", "Máxima",
                      "Síntese média (s)"], corpo)]
    duplas = sorted({int(r["dupla"]) for r in linhas})
    out += ["\n## Média por dupla\n",
            tabela_md(["Motor"] + [f"Dupla {d}" for d in duplas],
                      [[m] + [fmt(st.fmean(float(r["nota_1a5"]) for r in linhas
                                           if r["motor"] == m and int(r["dupla"]) == d), 2) for d in duplas]
                       for m in motores])]
    if len(motores) == 2:  # mesma frase dita pelos dois motores: comparação pareada por texto
        a, b = motores
        media = {(r["motor"], r["id"]): [] for r in linhas}
        for r in linhas:
            media[(r["motor"], r["id"])].append(float(r["nota_1a5"]))
        ids = sorted({r["id"] for r in linhas if r["motor"] == a} & {r["id"] for r in linhas if r["motor"] == b})
        dif = [st.fmean(media[(a, i)]) - st.fmean(media[(b, i)]) for i in ids]
        vit_a, vit_b, empates = sum(d > 1e-9 for d in dif), sum(d < -1e-9 for d in dif), sum(abs(d) <= 1e-9 for d in dif)
        out += ["\n## Comparação pareada (mesma frase nos dois motores)\n",
                f"Em {len(ids)} frases: `{a}` teve nota maior em {vit_a}, `{b}` em {vit_b} e houve empate em {empates}. "
                f"Diferença média ({a} menos {b}): {st.fmean(dif):+.2f} ponto na escala de 1 a 5.\n"]
    out += ["\n## Limites\n",
            "- Uma nota geral por áudio: não separa naturalidade de clareza, que o enunciado pede.",
            "- A nota de cada dupla já é uma média arredondada para inteiro (1 a 10); isso soma até ±0,22 ponto na escala de 1 a 5.",
            "- Os avaliadores são os integrantes do grupo e familiares, e não são independentes do trabalho.",
            "- 10 áudios por motor: diferenças pequenas entre os motores não são conclusivas."]
    return "\n".join(out)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--importar", metavar="NUMEROS", help="60 números separados por espaço (3 por áudio)")
    ap.add_argument("--forcar", action="store_true", help="sobrescreve as notas já importadas")
    a = ap.parse_args()
    if a.importar:
        if NOTAS.exists() and not a.forcar:
            print(f"{NOTAS.name} já existe: use --forcar para sobrescrever.")
            return 1
        try:
            linhas = importar(a.importar)
        except ValueError as e:
            print("Não importei:", e)
            return 1
        escrever_csv(NOTAS, linhas, ["aval", "dupla", "nota_1a10"])
        print(f"{len(linhas)} notas gravadas em {NOTAS}")
    if not NOTAS.exists():
        print(f"Falta {NOTAS.name}: rode com --importar.")
        return 1
    linhas = consolidar(ler_csv(NOTAS), ler_csv(CHAVE))
    tempos = ler_csv(EVIDENCIAS / "tts_tempos.csv") if (EVIDENCIAS / "tts_tempos.csv").exists() else None
    escrever_csv(EVIDENCIAS / "tts_notas.csv", linhas)
    (EVIDENCIAS / "tts_resumo.md").write_text(resumir(linhas, tempos), encoding="utf-8")
    print((EVIDENCIAS / "tts_resumo.md").read_text(encoding="utf-8"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
