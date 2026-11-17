"""Demonstra o POST do robô para a API: sobe a API simulada numa thread, roda o robô e confere o que chegou.

Uso: python demonstrar_api.py   (grava evidencias/api_simulada.txt)
O contrato da API está no topo de api_simulada.py; o 01-front-end deve implementar o mesmo.
"""
import tempfile
import threading
from pathlib import Path

import api_simulada
import config

DESTINO = config.RAIZ / "evidencias" / "api_simulada.txt"
tmp = Path(tempfile.mkdtemp())
config.SAIDA, config.BANCO, config.LOG = tmp, tmp / "p.db", tmp / "l.log"
config.RELATORIO, config.REVISAO = tmp / "r.json", tmp / "rev.csv"
config.OFFLINE = True  # só a notificação importa aqui; evita rede

servidor = api_simulada.criar_servidor(0)
porta = servidor.server_address[1]
threading.Thread(target=servidor.serve_forever, daemon=True).start()
config.API_URL = f"http://127.0.0.1:{porta}/protocolos"

import main  # noqa: E402

resumo = main.executar(config.ENTRADA)["resumo"]
recebidos = list(api_simulada.RECEBIDOS)
servidor.shutdown()
servidor.server_close()

linhas = [
    "Demonstração do POST robô -> API (API simulada em thread, porta local aleatória)",
    f"Robô: {resumo['protocolos']} protocolos gerados, {resumo['notificacoes_falhas']} notificações com falha",
    f"API: {len(recebidos)} protocolos recebidos por POST /protocolos",
    f"Primeiro: {recebidos[0] if recebidos else None} | Último: {recebidos[-1] if recebidos else None}",
    "Conferência: " + ("todos os protocolos chegaram" if len(recebidos) == resumo["protocolos"] else "DIVERGÊNCIA"),
]
DESTINO.write_text("\n".join(linhas) + "\n", encoding="utf-8")
print("\n".join(linhas))
