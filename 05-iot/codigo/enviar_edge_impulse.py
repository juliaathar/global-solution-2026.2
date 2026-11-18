"""Envia o dataset preparado ao Edge Impulse pela Ingestion API, já na categoria certa (Training ou Test).

A chave fica só na variável de ambiente EI_API_KEY (Dashboard > Keys do projeto). Nunca no código.

Uso:
    python enviar_edge_impulse.py            # só mostra o que seria enviado (padrão, não envia nada)
    set EI_API_KEY=ei_...                    # Windows (PowerShell: $env:EI_API_KEY="ei_...")
    python enviar_edge_impulse.py --enviar

Alternativa sem script: Data acquisition > Upload data, escolhendo a pasta training (categoria Training) e
depois a testing (categoria Testing), com "Infer from filename" no rótulo.
"""
import argparse
import csv
import os
import sys
import time

import requests

from comum import MANIFESTO, PREPARADOS

URL = "https://ingestion.edgeimpulse.com/api/{categoria}/files"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--enviar", action="store_true", help="envia de verdade (sem isso, só lista)")
    args = ap.parse_args()
    if not MANIFESTO.exists():
        sys.exit("Rode preparar_audios.py e verificar_dataset.py antes.")
    with open(MANIFESTO, encoding="utf-8") as f:
        itens = list(csv.DictReader(f))
    chave = os.getenv("EI_API_KEY", "")
    if args.enviar and not chave.startswith("ei_"):
        sys.exit("Defina EI_API_KEY com a chave do projeto (começa com ei_).")
    falhas = 0
    for m in itens:
        arq = PREPARADOS / m["arquivo"]
        if not args.enviar:
            print(f"[simulação] {m['conjunto']:8s} {m['classe']:13s} {arq.name}")
            continue
        for tentativa in range(3):
            try:
                with open(arq, "rb") as f:
                    r = requests.post(URL.format(categoria=m["conjunto"]), timeout=30,
                                      headers={"x-api-key": chave, "x-label": m["classe"]},
                                      files={"data": (arq.name, f, "audio/wav")})
                if r.status_code == 200:
                    print(f"ok  {m['conjunto']:8s} {arq.name}")
                    break
                print(f"erro {r.status_code} em {arq.name}: {r.text[:120]}")
            except requests.RequestException as e:
                print(f"falha de rede em {arq.name}: {e.__class__.__name__}")
            time.sleep(2 ** tentativa)
        else:
            falhas += 1
    if args.enviar:
        print(f"\n{len(itens) - falhas} enviados, {falhas} falharam. Confira em Data acquisition (Training e Test).")
    else:
        print(f"\n{len(itens)} arquivos seriam enviados. Use --enviar para mandar.")


if __name__ == "__main__":
    main()
