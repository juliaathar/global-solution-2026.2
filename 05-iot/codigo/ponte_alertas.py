"""Ponte OuviAí -> EloBairro: roda o modelo do Edge Impulse no microfone e avisa a API quando reconhece
campainha ou batida na porta. A API transforma o evento em alerta visual no app (01-front-end).

Privacidade: o áudio é processado só na memória deste aparelho, em janelas de 1 s. Nada é gravado e
nenhum áudio é enviado; a API recebe apenas {"classe", "confianca", "dispositivo"}.

Modos:
    python ponte_alertas.py --simular
        Manda uma sequência de eventos de teste (não precisa de microfone nem do modelo).
    python ponte_alertas.py --modelo ouviai.eim
        Roda o modelo exportado no Edge Impulse (Deployment > Linux (x86) ou Linux (AARCH64) / macOS).
        Funciona em Linux, macOS, Raspberry Pi e no WSL2 do Windows.
        Requer: pip install edge_impulse_linux pyaudio

Variáveis: API_URL (padrão http://localhost:8000), IOT_TOKEN (se a API exigir), IOT_LIMIAR (padrão 0.80).
"""
import argparse
import os
import sys
import time

import requests

API_URL = os.getenv("API_URL", "http://localhost:8000")
LIMIAR = float(os.getenv("IOT_LIMIAR", "0.80"))
INTERVALO_MIN_S = 3.0  # não manda o mesmo som duas vezes em menos de 3 s (uma campainha dura ~1-2 s)
SINONIMOS = {"campainha": "campainha", "batida_porta": "batida_porta", "batida": "batida_porta",
             "batida na porta": "batida_porta", "batida_na_porta": "batida_porta", "ambiente": "ambiente",
             "ruido": "ambiente", "noise": "ambiente"}


def enviar(classe: str, confianca: float, dispositivo: str) -> None:
    try:
        r = requests.post(f"{API_URL}/iot/eventos", timeout=5,
                          json={"classe": classe, "confianca": round(confianca, 3), "dispositivo": dispositivo},
                          headers={"X-Dispositivo-Token": os.getenv("IOT_TOKEN", "")})
        if r.status_code == 201:
            d = r.json()
            print(f"  -> API: {d['icone']} {d['mensagem']} ({d['motivo']})")
        else:
            print(f"  -> API respondeu {r.status_code}: {r.text[:100]}")
    except requests.RequestException as e:  # a API fora do ar não derruba a escuta
        print(f"  -> API indisponível ({e.__class__.__name__}); seguindo a escuta")


def simular(dispositivo: str) -> None:
    sequencia = [("ambiente", 0.97), ("campainha", 0.93), ("campainha", 0.95), ("batida_porta", 0.71),
                 ("batida_porta", 0.90), ("ambiente", 0.88)]
    for classe, conf in sequencia:
        print(f"{classe} {conf:.0%}")
        enviar(classe, conf, dispositivo)
        time.sleep(1.5)


def escutar(modelo: str, dispositivo: str, microfone: int | None) -> None:
    try:
        from edge_impulse_linux.audio import AudioImpulseRunner
    except ImportError:
        sys.exit("Instale: pip install edge_impulse_linux pyaudio   (Linux, macOS, Raspberry Pi ou WSL2)")
    ultimo: dict[str, float] = {}
    with AudioImpulseRunner(os.path.abspath(modelo)) as runner:
        info = runner.init()
        rotulos = info["model_parameters"]["labels"]
        print(f"Modelo: {info['project']['name']} | rótulos: {rotulos} | limiar {LIMIAR:.0%}. Ctrl+C para parar.")
        for res, _audio in runner.classifier(device_id=microfone):
            notas = res["result"]["classification"]
            rotulo, conf = max(notas.items(), key=lambda kv: kv[1])
            classe = SINONIMOS.get(rotulo.strip().lower())
            ms = res["timing"]["dsp"] + res["timing"]["classification"]
            print(f"{rotulo:14s} {conf:5.0%}  ({ms} ms)", end="\r")
            if classe in (None, "ambiente") or conf < LIMIAR:
                continue  # ambiente e incerteza ficam no aparelho: não geram tráfego nem alerta
            agora = time.monotonic()
            if agora - ultimo.get(classe, 0) >= INTERVALO_MIN_S:
                ultimo[classe] = agora
                print(f"\n{classe} {conf:.0%}")
                enviar(classe, conf, dispositivo)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--simular", action="store_true")
    g.add_argument("--modelo", help="arquivo .eim exportado do Edge Impulse")
    ap.add_argument("--dispositivo", default="sala")
    ap.add_argument("--microfone", type=int, default=None, help="id do microfone (o SDK lista se omitido)")
    a = ap.parse_args()
    try:
        simular(a.dispositivo) if a.simular else escutar(a.modelo, a.dispositivo, a.microfone)
    except KeyboardInterrupt:
        print("\nEncerrado.")


if __name__ == "__main__":
    main()
