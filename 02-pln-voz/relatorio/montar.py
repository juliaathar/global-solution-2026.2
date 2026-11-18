"""Monta o relatório: coloca os resumos de evidencias/ no lugar dos marcadores.

    python relatorio/montar.py                     # gera relatorio/relatorio_montado.md
    python relatorio/montar.py --sem-instrucoes    # também remove os blocos "Escrever" e "Como usar"

Marcador no relatorio.md:  <!-- INCLUIR: evidencias/stt_resumo.md -->
Se o arquivo ainda não existe, o marcador vira um aviso visível. O script lista o que falta.
"""
import argparse
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
MARCADOR = re.compile(r"<!--\s*INCLUIR:\s*(\S+?)\s*-->")
PENDENCIA = re.compile(r"\[PREENCHER")
NIVEL_EXTRA = 3  # os resumos começam em '#'; dentro de uma subseção '###' ficam em '####'


def rebaixar_titulos(texto: str, niveis: int = NIVEL_EXTRA) -> str:
    return re.sub(r"^(#{1,6})(?=\s)", lambda m: "#" * min(6, len(m.group(1)) + niveis), texto, flags=re.M)


def remover_instrucoes(texto: str) -> str:
    """Remove os blocos de citação que começam com **Escrever**, **Como usar** ou **Rascunho**."""
    saida, pulando = [], False
    for linha in texto.splitlines():
        if linha.startswith(">"):
            if re.match(r">\s*\*\*(Escrever|Como usar|Rascunho)", linha):
                pulando = True
            if pulando:
                continue
        else:
            if pulando and not linha.strip():
                pulando = False
                continue  # descarta a linha em branco depois do bloco
            pulando = False
        saida.append(linha)
    return "\n".join(saida) + "\n"


def montar(texto: str, raiz: Path, sem_instrucoes: bool = False) -> tuple[str, list[str], int]:
    """Retorna (texto montado, evidências que faltam, nº de marcadores [PREENCHER] restantes)."""
    faltando = []

    def trocar(m: re.Match) -> str:
        caminho = raiz / m.group(1)
        if caminho.is_file():
            return rebaixar_titulos(caminho.read_text(encoding="utf-8").strip())
        faltando.append(m.group(1))
        return f"**[FALTA: {m.group(1)} ainda não existe. Rode o script de avaliação correspondente.]**"

    texto = MARCADOR.sub(trocar, texto)
    if sem_instrucoes:
        texto = remover_instrucoes(texto)
    return texto, faltando, len(PENDENCIA.findall(texto))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sem-instrucoes", action="store_true")
    ap.add_argument("--entrada", type=Path, default=RAIZ / "relatorio" / "relatorio.md")
    ap.add_argument("--saida", type=Path, default=RAIZ / "relatorio" / "relatorio_montado.md")
    a = ap.parse_args()

    texto, faltando, pendencias = montar(a.entrada.read_text(encoding="utf-8"), RAIZ, a.sem_instrucoes)
    a.saida.write_text(texto, encoding="utf-8")
    print(f"Gerado: {a.saida}")
    print(f"Pendências [PREENCHER]: {pendencias}")
    if faltando:
        print("Evidências que faltam:\n  " + "\n  ".join(faltando))
    return 0


if __name__ == "__main__":
    sys.exit(main())
