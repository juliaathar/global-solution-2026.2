"""Converte as gravações para o formato do enunciado e separa Training/Test sem reuso.

Entrada:  dados_audio/brutos/<classe>/*  (wav, m4a, mp3, ogg, webm, 3gp...; uma pasta por classe)
Saída:    dados_audio/preparados/{training,testing}/<classe>.<nn>.wav   (16 kHz, mono, PCM16, 5,0 s)
          dados_audio/manifesto.csv   (arquivo, classe, conjunto, níveis de áudio e impressão digital)

Regras:
- Exatamente 20 gravações por classe: 15 para Training e 5 para Test, sorteadas com semente fixa (42).
- Gravação com mais de 5 s é cortada no trecho de maior energia (onde o som está); com menos, completada com silêncio.
- Duas gravações idênticas (mesma impressão digital) param o script: seria reuso entre Training e Test.
- O nome do arquivo começa pelo rótulo (ex.: campainha.03.wav), que é como o Edge Impulse infere a classe.

Uso (a partir de 05-iot/codigo):   python preparar_audios.py
Precisa do ffmpeg no PATH para arquivos que não sejam WAV 16 kHz (Windows: winget install ffmpeg).
"""
import argparse
import csv
import random
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np

from comum import (BRUTOS, CLASSES, DURACAO_S, MANIFESTO, POR_CLASSE, PREPARADOS, SEMENTE, TAXA, TESTE, TREINO,
                   gravar_wav, ler_wav, niveis_dbfs, sha1_amostras)

EXTENSOES = {".wav", ".m4a", ".mp3", ".ogg", ".webm", ".3gp", ".aac", ".flac", ".opus"}
SILENCIO_DBFS = -50.0   # RMS abaixo disso: provavelmente gravou nada
SATURACAO_DBFS = -0.1   # pico acima disso: provavelmente estourou


def carregar(arq: Path) -> np.ndarray:
    """Lê qualquer formato e devolve int16 mono 16 kHz."""
    if arq.suffix.lower() == ".wav":
        try:
            x, taxa, _, _ = ler_wav(arq)
            if taxa == TAXA:
                return x
        except (ValueError, EOFError):
            pass  # WAV em 24/32 bits ou float: deixa o ffmpeg converter
    if not shutil.which("ffmpeg"):
        sys.exit(f"{arq.name} precisa de conversão e o ffmpeg não foi encontrado. Instale o ffmpeg e rode de novo.")
    with tempfile.TemporaryDirectory() as tmp:
        saida = Path(tmp) / "x.wav"
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(arq), "-ac", "1", "-ar", str(TAXA),
                        "-sample_fmt", "s16", str(saida)], check=True)
        return ler_wav(saida)[0]


def ajustar_duracao(x: np.ndarray) -> tuple[np.ndarray, str]:
    alvo = int(TAXA * DURACAO_S)
    if len(x) == alvo:
        return x, ""
    if len(x) < alvo:
        return np.concatenate([x, np.zeros(alvo - len(x), dtype=np.int16)]), f"completado {alvo - len(x)} amostras"
    energia = np.convolve(x.astype(np.float64) ** 2, np.ones(alvo), mode="valid")  # janela de 5 s com mais som
    ini = int(np.argmax(energia))
    return x[ini:ini + alvo], f"cortado de {len(x) / TAXA:.1f} s a partir de {ini / TAXA:.1f} s"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--entrada", type=Path, default=BRUTOS)
    ap.add_argument("--saida", type=Path, default=PREPARADOS)
    args = ap.parse_args()

    linhas, digitais, problemas = [], {}, []
    rnd = random.Random(SEMENTE)
    for classe in CLASSES:
        pasta = args.entrada / classe
        arquivos = sorted(p for p in pasta.glob("*") if p.suffix.lower() in EXTENSOES) if pasta.is_dir() else []
        if len(arquivos) != POR_CLASSE:
            problemas.append(f"{classe}: {len(arquivos)} gravações em {pasta} (precisa de exatamente {POR_CLASSE})")
            continue
        ordem = list(range(POR_CLASSE))
        rnd.shuffle(ordem)
        teste = set(ordem[:TESTE])
        for i, arq in enumerate(arquivos):
            x, nota = ajustar_duracao(carregar(arq))
            digital = sha1_amostras(x)
            if digital in digitais:
                sys.exit(f"Gravação repetida: {arq} é igual a {digitais[digital]}. Grave de novo.")
            digitais[digital] = arq
            conjunto = "testing" if i in teste else "training"
            destino = args.saida / conjunto / f"{classe}.{i + 1:02d}.wav"
            gravar_wav(destino, x)
            pico, rms = niveis_dbfs(x)
            avisos = [nota] if nota else []
            if rms < SILENCIO_DBFS:
                avisos.append("muito baixo, confira se gravou o som")
            if pico >= SATURACAO_DBFS:
                avisos.append("saturado (estourou)")
            linhas.append({"arquivo": destino.relative_to(args.saida).as_posix(), "original": arq.name,
                           "classe": classe, "conjunto": conjunto, "taxa_hz": TAXA, "canais": 1, "bits": 16,
                           "duracao_s": DURACAO_S, "pico_dbfs": pico, "rms_dbfs": rms, "sha1": digital,
                           "avisos": "; ".join(avisos)})
    if problemas:
        sys.exit("Faltam gravações:\n- " + "\n- ".join(problemas))

    MANIFESTO.parent.mkdir(parents=True, exist_ok=True)
    with open(MANIFESTO, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(linhas[0]))
        w.writeheader()
        w.writerows(linhas)
    for classe in CLASSES:
        tr = sum(l["classe"] == classe and l["conjunto"] == "training" for l in linhas)
        print(f"{classe:13s} training={tr}  testing={POR_CLASSE - tr}")
    com_aviso = [l for l in linhas if l["avisos"]]
    for l in com_aviso:
        print(f"  aviso {l['arquivo']}: {l['avisos']}")
    print(f"\n{len(linhas)} arquivos em {args.saida}  ·  manifesto em {MANIFESTO}")
    print(f"Proximo passo: python verificar_dataset.py   (deve dar {TREINO}/{TESTE} por classe)")


if __name__ == "__main__":
    main()
