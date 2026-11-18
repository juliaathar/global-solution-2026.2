"""Funções comuns dos scripts de avaliação (CSV, médias, tabelas em Markdown)."""
import csv
import re
import statistics
import sys
import unicodedata
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

EVIDENCIAS = RAIZ / "evidencias"
AUDIOS = RAIZ / "audios_teste"
TESTES = RAIZ / "testes"


def ler_csv(caminho: Path) -> list[dict]:
    with open(caminho, newline="", encoding="utf-8-sig") as f:
        return [{k: (v or "").strip() for k, v in linha.items()} for linha in csv.DictReader(f)]


def escrever_csv(caminho: Path, linhas: list[dict], campos: list[str] | None = None) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    campos = campos or list(linhas[0].keys())
    with open(caminho, "w", newline="", encoding="utf-8-sig") as f:  # utf-8-sig: o Excel abre sem quebrar acentos
        w = csv.DictWriter(f, fieldnames=campos, extrasaction="ignore")
        w.writeheader()
        w.writerows(linhas)


def media(valores: list[float]) -> float:
    return statistics.fmean(valores) if valores else float("nan")


def fmt(x: float, casas: int = 3) -> str:
    return "n/d" if x != x else f"{x:.{casas}f}"


def pct(x: float) -> str:
    return "n/d" if x != x else f"{100 * x:.1f}%"


def tabela_md(cabecalho: list[str], linhas: list[list]) -> str:
    out = ["| " + " | ".join(cabecalho) + " |", "|" + "|".join("---" for _ in cabecalho) + "|"]
    out += ["| " + " | ".join(str(c) for c in l) + " |" for l in linhas]
    return "\n".join(out)


def sem_acento(s: str) -> str:
    s = unicodedata.normalize("NFD", s.lower())
    return "".join(c for c in s if unicodedata.category(c) != "Mn")


def so_palavras(s: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^\w\s]", " ", s.lower())).strip()
