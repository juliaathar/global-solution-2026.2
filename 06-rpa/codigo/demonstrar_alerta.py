"""Demonstra o alerta do Inmet elevando a urgência, com data fixa (16/11/2026 12:00) e o snapshot do feed.

Assim a evidência não depende de haver aviso vigente no dia em que o robô roda.
Uso: python demonstrar_alerta.py   (grava evidencias/alerta_inmet.txt)
"""
import csv
import tempfile
from datetime import datetime
from pathlib import Path

import config
import enriquecimento
from coleta_inmet import coletar_avisos as coletar_real

DESTINO = config.RAIZ / "evidencias" / "alerta_inmet.txt"
AGORA = datetime(2026, 11, 16, 12, 0)
tmp = Path(tempfile.mkdtemp())
config.SAIDA, config.BANCO, config.LOG = tmp, tmp / "p.db", tmp / "l.log"
config.RELATORIO, config.REVISAO = tmp / "r.json", tmp / "rev.csv"
config.OFFLINE = True
enriquecimento.coletar_avisos = lambda: coletar_real(agora=AGORA)  # congela o "agora" no momento do snapshot

import main  # noqa: E402

# entrada = dados sintéticos + 2 relatos preventivos (bueiro entupido sem água subindo), que saem como urgência média
extras = [("E1", "A boca de lobo da esquina está cheia de folhas e a água não escoa direito"),
          ("E2", "Bueiro da Rua Sete entupido de folhas, a água da chuva não escoa")]
entrada = tmp / "entrada.csv"
with open(config.ENTRADA, newline="", encoding="utf-8") as f:
    leitor = list(csv.DictReader(f))
campos = list(leitor[0])
with open(entrada, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=campos)
    w.writeheader()
    w.writerows(leitor)
    w.writerows({"id": i, "texto": t, **{c: "" for c in campos if c not in ("id", "texto")}} for i, t in extras)
resultado = main.executar(entrada)
alag = [p for p in resultado["protocolos"] if p["categoria"] == "alagamento"]
com_alerta = [p for p in alag if p["alerta_inmet"]]
elevados = [p for p in com_alerta if p["urgencia_original"] != "alta" and p["urgencia"] == "alta"]
linhas = [
    f"Demonstração com data fixa {AGORA:%d/%m/%Y %H:%M} e snapshot do feed do Inmet (origem: {resultado['resumo']['inmet_origem']})",
    f"Avisos vigentes para {config.INMET_AREA}: {resultado['resumo']['avisos_vigentes']}",
    f"Relatos de alagamento com protocolo: {len(alag)} | com alerta anexado: {len(com_alerta)} | urgência elevada pelo alerta (média -> alta): {len(elevados)}",
    f"Exemplo: {com_alerta[0]['id']} -> {com_alerta[0]['alerta_inmet']}" if com_alerta else "Sem exemplo",
    *[f"Elevado: {p['id']} urgência {p['urgencia_original']} -> {p['urgencia']} ({p['alerta_inmet']})" for p in elevados],
    "Obs.: alagamento já sai com urgência alta pelo classificador; o alerta altera o resultado só nos casos preventivos.",
]
DESTINO.write_text("\n".join(linhas) + "\n", encoding="utf-8")
print("\n".join(linhas))
