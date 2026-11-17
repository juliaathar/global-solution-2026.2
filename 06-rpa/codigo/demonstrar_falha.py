"""Demonstra falhas tratadas: API fora do ar (retry com espera) e arquivo ausente.

Uso: python demonstrar_falha.py   (grava evidencias/falha_tratada.txt)
"""
import logging
import tempfile
from pathlib import Path

import config

DESTINO = config.RAIZ / "evidencias" / "falha_tratada.txt"
DESTINO.parent.mkdir(exist_ok=True)
tmp = Path(tempfile.mkdtemp())
config.SAIDA, config.BANCO = tmp, tmp / "p.db"
config.LOG, config.RELATORIO, config.REVISAO = tmp / "l.log", tmp / "r.json", tmp / "rev.csv"
config.API_URL = "http://127.0.0.1:9/protocolos"  # porta fechada: simula API fora do ar
config.TIMEOUT_S, config.ESPERA_BASE_S = 1, 0.2

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s",
                    handlers=[logging.FileHandler(DESTINO, "w", encoding="utf-8"), logging.StreamHandler()])
import main  # noqa: E402

log = logging.getLogger("demo")
log.info("CENARIO 1: arquivo de entrada ausente")
r1 = main.executar(Path("nao_existe.csv"))["resumo"]
log.info("CENARIO 2: API do app fora do ar (retry e segue sem notificar)")
sem = Path(tmp / "dois.csv")
sem.write_text("id,texto\nD1,Buraco perigoso na Rua Sete com risco de acidente\n"
               "D2,Poste apagado na Av. Brasil ha duas semanas\n", encoding="utf-8")
r2 = main.executar(sem)["resumo"]
import coleta_web  # noqa: E402

log.info("CENARIO 3: site fora do ar na coleta de UBS (cai no snapshot local)")
u, origem = coleta_web.coletar_ubs("http://127.0.0.1:9/ubs")
log.info("UBS: %d unidades, origem=%s", len(u), origem)
log.info("CENARIO 4: robots.txt proibe o acesso (portal de dados da prefeitura de SP, Disallow: /)")
u, origem = coleta_web.coletar_ubs("https://dados.prefeitura.sp.gov.br/")
log.info("UBS: %d unidades, origem=%s", len(u), origem)
log.info("CENARIO 5: HTML mudou e os seletores nao acham nada (pagina sem UBS)")
orig, coleta_web.baixar = coleta_web.baixar, lambda *a, **k: "<html><body><p>layout novo</p></body></html>"
u, origem = coleta_web.coletar_ubs()
coleta_web.baixar = orig
log.info("UBS: %d unidades, origem=%s", len(u), origem)
import coleta_inmet  # noqa: E402
import coleta_noticias  # noqa: E402

log.info("CENARIO 6: feed do Inmet fora do ar (usa snapshot do feed)")
config.INMET_URL = "http://127.0.0.1:9/avisos/rss"
_, origem = coleta_inmet.coletar_avisos()
log.info("Inmet: origem=%s", origem)
log.info("CENARIO 7: feed do Inmet devolve XML invalido")
orig_baixar, coleta_inmet.baixar = coleta_inmet.baixar, lambda *a, **k: "<rss><channel><item>"
_, origem = coleta_inmet.coletar_avisos()
coleta_inmet.baixar = orig_baixar
log.info("Inmet: origem=%s", origem)
log.info("CENARIO 8: crawler perde a pagina 2 (mantem a pagina 1 ja coletada)")
doc1 = config.NOTICIAS_SNAPSHOTS[0].read_text(encoding="utf-8", errors="replace")
chamadas = []


def pagina_instavel(url):
    chamadas.append(url)
    if len(chamadas) == 1:
        return doc1
    raise coleta_web.ErroColeta("timeout simulado na pagina 2")


noticias, info = coleta_noticias.rastrear(max_paginas=3, baixar_fn=pagina_instavel)
log.info("Crawler: %d noticias, info=%s", len(noticias), info)
log.info("CENARIO 9: servidor de e-mail (SMTP) fora do ar (retry e segue sem notificar; nenhum e-mail real e enviado)")
config.API_URL = ""
config.SMTP_HOST, config.SMTP_PORTA = "127.0.0.1", 9
config.SMTP_USUARIO, config.SMTP_SENHA, config.EMAIL_DESTINO = "robo@exemplo.com", "senha-ficticia", "gestor@exemplo.com"
config.EMAIL_ATIVO = True
sem3 = Path(tmp / "tres.csv")
sem3.write_text("id,texto\nE1,Bueiro entupido e agua entrando nas casas da Rua Sete\n", encoding="utf-8")
import notificador  # noqa: E402
notificador._entregues.clear()
r9 = main.executar(sem3)["resumo"]
log.info("Resultado e-mail: notificacoes_falhas=%s", r9["notificacoes_falhas"])
log.info("Resultado: cenario1=%s | cenario2=%s", r1, r2)
