"""Confere o dataset preparado antes de enviar ao Edge Impulse e grava evidencias/verificacao_dataset.md.

Checa, arquivo por arquivo (lendo o WAV, não confiando no manifesto):
- 16 kHz, mono, PCM 16 bits, 5,0 s
- rótulo no nome do arquivo igual à pasta do manifesto
- 15 em training e 5 em testing por classe
- nenhuma gravação igual em training e testing (impressão digital das amostras)

Uso:  python verificar_dataset.py        (código de saída 1 se algo falhar)
"""
import csv
import sys
from collections import Counter
from datetime import datetime

from comum import (CLASSES, DURACAO_S, EVIDENCIAS, MANIFESTO, PREPARADOS, TAXA, TESTE, TREINO, ler_wav,
                   niveis_dbfs, sha1_amostras)


def verificar() -> tuple[list[str], list[str], Counter]:
    erros, linhas_md = [], []
    if not MANIFESTO.exists():
        return [f"Manifesto não encontrado ({MANIFESTO}). Rode preparar_audios.py."], [], Counter()
    with open(MANIFESTO, encoding="utf-8") as f:
        manifesto = list(csv.DictReader(f))
    contagem, digitais = Counter(), {}
    for m in manifesto:
        arq = PREPARADOS / m["arquivo"]
        if not arq.exists():
            erros.append(f"{m['arquivo']}: arquivo não existe")
            continue
        x, taxa, canais, bits = ler_wav(arq)
        dur = len(x) / taxa
        rotulo = arq.name.split(".")[0]
        ok = taxa == TAXA and canais == 1 and bits == 16 and abs(dur - DURACAO_S) < 1e-6 and rotulo == m["classe"]
        if not ok:
            erros.append(f"{m['arquivo']}: {taxa} Hz, {canais} canal(is), {bits} bits, {dur:.2f} s, rótulo '{rotulo}'")
        d = sha1_amostras(x)
        if d in digitais:
            erros.append(f"{m['arquivo']} é igual a {digitais[d]} (reuso)")
        digitais[d] = m["arquivo"]
        contagem[(m["classe"], m["conjunto"])] += 1
        pico, rms = niveis_dbfs(x)
        linhas_md.append(f"| {m['arquivo']} | {m['classe']} | {m['conjunto']} | {taxa} | {canais} | {bits} | "
                         f"{dur:.1f} | {pico} | {rms} | {'✅' if ok else '❌'} |")
    for c in CLASSES:
        if contagem[(c, "training")] != TREINO or contagem[(c, "testing")] != TESTE:
            erros.append(f"{c}: {contagem[(c, 'training')]} training / {contagem[(c, 'testing')]} testing "
                         f"(esperado {TREINO}/{TESTE})")
    return erros, linhas_md, contagem


def main() -> None:
    erros, linhas, contagem = verificar()
    resumo = "\n".join(f"| {c} | {contagem[(c, 'training')]} | {contagem[(c, 'testing')]} |" for c in CLASSES)
    md = (f"# Verificação do dataset do OuviAí\n\nGerado por `codigo/verificar_dataset.py` em "
          f"{datetime.now():%d/%m/%Y %H:%M}.\n\n**Resultado:** "
          f"{'✅ tudo certo' if not erros else '❌ ' + str(len(erros)) + ' problema(s)'}\n\n"
          f"| Classe | Training | Test |\n|---|---|---|\n{resumo}\n\n"
          + ("## Problemas\n\n" + "\n".join(f"- {e}" for e in erros) + "\n\n" if erros else "")
          + "## Arquivos\n\n| Arquivo | Classe | Conjunto | Hz | Canais | Bits | s | Pico dBFS | RMS dBFS | OK |\n"
            "|---|---|---|---|---|---|---|---|---|---|\n" + "\n".join(linhas) + "\n")
    EVIDENCIAS.mkdir(exist_ok=True)
    (EVIDENCIAS / "verificacao_dataset.md").write_text(md, encoding="utf-8")
    print(md.split("## Arquivos")[0])
    sys.exit(1 if erros else 0)


if __name__ == "__main__":
    main()
