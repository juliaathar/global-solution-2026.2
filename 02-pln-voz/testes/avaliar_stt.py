"""Avalia o STT: WER com jiwer, latência, comparação entre modelos e análise de viés.

    python testes/avaliar_stt.py --modelos base small

Lê audios_teste/manifesto_stt.csv e grava evidencias/stt_resultados.csv e stt_resumo.md.
Os áudios de teste NÃO são apagados (são do grupo, com consentimento de quem gravou).
"""
import argparse
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from util import (AUDIOS, EVIDENCIAS, escrever_csv, fmt, ler_csv, media,  # noqa: E402
                  tabela_md)

from adaptacao_fala import numero_por_extenso  # noqa: E402

SIGLAS = ["ubs", "upa", "cras", "creas", "cpf", "rg", "cep", "inss", "sus", "samu", "cnh"]
EIXOS_VIES = [("falante", "Falante"), ("ruido", "Ruído de fundo"),
              ("faixa_etaria", "Faixa etária"), ("sotaque", "Sotaque / região")]


def normalizar(texto: str) -> str:
    """Deixa referência e transcrição comparáveis: minúsculas, sem pontuação,
    números por extenso e siglas coladas ('u b s' vira 'ubs')."""
    t = texto.lower()
    t = re.sub(r"r\$\s*(\d+)", r"\1 reais", t)
    t = t.replace("%", " por cento ")
    t = re.sub(r"\d+", lambda m: f" {numero_por_extenso(int(m.group(0)))} " if len(m.group(0)) < 10
               else m.group(0), t)
    t = re.sub(r"\bh\b", "horas", t)  # '7h' -> 'sete horas'
    t = re.sub(r"[^\w\s]", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    for s in SIGLAS:
        t = re.sub(r"\b" + r"\s".join(s) + r"\b", s, t)  # 'u b s' -> 'ubs'
    return t


def wer(referencia: str, hipotese: str) -> float:
    import jiwer
    return jiwer.wer(normalizar(referencia), normalizar(hipotese))


def wer_global(refs: list[str], hips: list[str]) -> float:
    import jiwer
    return jiwer.wer([normalizar(r) for r in refs], [normalizar(h) for h in hips])


def arquivos_faltando(linhas: list[dict], pasta: Path) -> list[str]:
    return [l["arquivo"] for l in linhas if not (pasta / l["arquivo"]).is_file()]


def avaliar(stts: dict, linhas: list[dict], pasta: Path) -> list[dict]:
    """Roda cada STT em cada áudio. `stts` mapeia nome do modelo -> objeto com .transcrever()."""
    resultados = []
    for nome, stt in stts.items():
        for l in linhas:
            t = time.perf_counter()
            hip = stt.transcrever(str(pasta / l["arquivo"]))
            dt = time.perf_counter() - t
            resultados.append({**l, "modelo": nome, "transcricao": hip,
                               "wer": round(wer(l["referencia"], hip), 4), "latencia_s": round(dt, 3)})
    return resultados


def resumir(resultados: list[dict]) -> str:
    modelos = list(dict.fromkeys(r["modelo"] for r in resultados))
    out = ["# STT: resultados\n"]

    linhas = []
    for m in modelos:
        rs = [r for r in resultados if r["modelo"] == m]
        linhas.append([m, len(rs),
                       fmt(wer_global([r["referencia"] for r in rs], [r["transcricao"] for r in rs])),
                       fmt(media([r["wer"] for r in rs])),
                       fmt(media([r["latencia_s"] for r in rs]), 2)])
    out += ["## Comparação entre modelos\n",
            tabela_md(["Modelo", "Áudios", "WER global", "WER médio por áudio", "Latência média (s)"], linhas),
            "\nWER global soma os erros de todas as palavras. Quanto menor, melhor.\n"]

    for chave, titulo in EIXOS_VIES:
        valores = sorted({r.get(chave, "") for r in resultados if r.get(chave, "")})
        if len(valores) < 2:
            continue
        linhas = []
        for v in valores:
            linha = [v]
            for m in modelos:
                rs = [r for r in resultados if r["modelo"] == m and r.get(chave) == v]
                linha.append(f"{fmt(media([r['wer'] for r in rs]))} (n={len(rs)})")
            linhas.append(linha)
        out += [f"## Viés: {titulo}\n", tabela_md([titulo] + [f"WER {m}" for m in modelos], linhas), ""]

    piores = sorted(resultados, key=lambda r: -r["wer"])[:5]
    out += ["## Cinco piores transcrições\n",
            tabela_md(["Modelo", "Arquivo", "WER", "Referência", "Transcrição"],
                      [[r["modelo"], r["arquivo"], fmt(r["wer"]), r["referencia"], r["transcricao"]]
                       for r in piores])]
    return "\n".join(out)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--modelos", nargs="+", default=["base", "small"])
    ap.add_argument("--manifesto", type=Path, default=AUDIOS / "manifesto_stt.csv")
    ap.add_argument("--pasta", type=Path, default=AUDIOS / "stt")
    ap.add_argument("--saida", type=Path, default=EVIDENCIAS, help="pasta dos resultados")
    a = ap.parse_args()

    linhas = ler_csv(a.manifesto)
    faltando = arquivos_faltando(linhas, a.pasta)
    if faltando:
        print(f"Faltam {len(faltando)} áudios em {a.pasta}:\n  " + "\n  ".join(faltando))
        return 1

    from stt import WhisperSTT
    stts = {f"faster-whisper-{m}": WhisperSTT(m, apagar_audio=False) for m in a.modelos}
    resultados = avaliar(stts, linhas, a.pasta)
    a.saida.mkdir(parents=True, exist_ok=True)
    escrever_csv(a.saida / "stt_resultados.csv", resultados)
    (a.saida / "stt_resumo.md").write_text(resumir(resultados), encoding="utf-8")
    print((a.saida / "stt_resumo.md").read_text(encoding="utf-8"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
