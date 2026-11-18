"""Opcional: grava os clipes de 5 s pelo microfone do computador, já em 16 kHz, mono, PCM16.

O caminho principal é gravar pelo celular no próprio Edge Impulse (Data acquisition > Connect a device >
Use your mobile phone). Use este script só se preferir gravar no computador e enviar depois.

Uso:   pip install sounddevice numpy
       python gravar_no_pc.py campainha       # grava 20 clipes de campainha, com contagem regressiva
Os arquivos vão para dados_audio/brutos/<classe>/ (pasta não versionada). Depois: python preparar_audios.py
"""
import sys
import time

import numpy as np

from comum import BRUTOS, CLASSES, DURACAO_S, POR_CLASSE, TAXA, gravar_wav


def main() -> None:
    if len(sys.argv) != 2 or sys.argv[1] not in CLASSES:
        sys.exit(f"Uso: python gravar_no_pc.py <{'|'.join(CLASSES)}>")
    import sounddevice as sd
    classe = sys.argv[1]
    pasta = BRUTOS / classe
    ja = len(list(pasta.glob("*.wav"))) if pasta.exists() else 0
    print(f"Gravando {classe}: {ja} já existem; faltam {max(0, POR_CLASSE - ja)}. Ctrl+C para parar.")
    for n in range(ja + 1, POR_CLASSE + 1):
        input(f"\n[{n}/{POR_CLASSE}] Enter para gravar 5 s... ")
        for s in (3, 2, 1):
            print(s, end=" ", flush=True)
            time.sleep(0.6)
        print("GRAVANDO")
        x = sd.rec(int(TAXA * DURACAO_S), samplerate=TAXA, channels=1, dtype="int16")
        sd.wait()
        gravar_wav(pasta / f"{classe}.{n:02d}.wav", np.asarray(x).reshape(-1))
        print("ok")


if __name__ == "__main__":
    main()
