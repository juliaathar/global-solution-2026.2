"""Gera notebooks/demonstracao.ipynb (execução completa do robô, célula a célula).

Uso: python gerar_notebook.py     (e depois abra o .ipynb no Jupyter ou no Colab)
O notebook usa só a biblioteca padrão + as dependências do requirements.txt e roda offline por padrão.
"""
import json
from pathlib import Path

import config

SAIDA = config.RAIZ / "notebooks" / "demonstracao.ipynb"


def md(texto):
    return {"cell_type": "markdown", "metadata": {}, "source": texto.strip("\n").splitlines(keepends=True)}


def code(texto):
    return {"cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [],
            "source": texto.strip("\n").splitlines(keepends=True)}


CELULAS = [
    md("""
# Robô RPA do EloBairro: demonstração ponta a ponta
Valida, deduplica, classifica e protocola relatos de moradores, consulta fontes públicas (UBS, alertas do Inmet) e notifica.
Este notebook roda **offline por padrão** (usa os snapshots das páginas públicas); troque `USAR_REDE` para buscar na web de verdade.
"""),
    md("## 1. Preparação"),
    code("""
import os, sys, subprocess, tempfile
from pathlib import Path

USAR_REDE = False   # True = busca UBS e avisos do Inmet na web de verdade

# No Colab: clona a branch do projeto e instala as dependências. Localmente: usa a pasta do repositório.
if not any(p.name == "06-rpa" for p in [Path.cwd(), *Path.cwd().parents]):
    if not Path("global-solution-2026.2").exists():
        subprocess.run(["git", "clone", "-b", "edgar", "https://github.com/juliaathar/global-solution-2026.2"], check=True)
    os.chdir("global-solution-2026.2/06-rpa/notebooks")
subprocess.run([sys.executable, "-m", "pip", "install", "-q", "-r", "../requirements.txt"], check=True)

RAIZ = next(p for p in [Path.cwd(), *Path.cwd().parents] if p.name == "06-rpa")
sys.path.insert(0, str(RAIZ / "codigo"))

import config
tmp = Path(tempfile.mkdtemp())  # tudo que o robô gravar vai para uma pasta temporária
config.SAIDA, config.BANCO, config.LOG = tmp, tmp / "p.db", tmp / "execucao.log"
config.RELATORIO, config.REVISAO, config.HISTORICO = tmp / "r.json", tmp / "rev.csv", tmp / "hist.jsonl"
config.OFFLINE = not USAR_REDE
print("Pasta de saída:", tmp, "| rede:", USAR_REDE)
"""),
    md("## 2. Entrada: relatos sintéticos rotulados\nSão 120 relatos mais 5 casos problemáticos (duplicado, vazio, curto, longo, ambíguo). Nenhum dado pessoal real."),
    code("""
import csv
import gerar_dados
entrada = tmp / "relatos.csv"
with open(entrada, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["id", "texto", "categoria_real", "urgencia_real", "ubs_real"])
    w.writeheader(); w.writerows(gerar_dados.gerar())
linhas = list(csv.DictReader(open(entrada, encoding="utf-8")))
print(len(linhas), "linhas. Exemplos:")
for r in linhas[:3]: print(" ", r["id"], r["texto"])
"""),
    md("## 3. Execução do robô\nIngestão, validação, máscara de dados pessoais, deduplicação, classificação, enriquecimento (UBS e Inmet), protocolo e notificação."),
    code("""
import main
resultado = main.executar(entrada)
for chave, valor in resultado["resumo"].items(): print(f"{chave:28} {valor}")
"""),
    md("## 4. Um protocolo de cada categoria"),
    code("""
vistas = set()
for p in resultado["protocolos"]:
    if p["categoria"] not in vistas:
        vistas.add(p["categoria"])
        print(p["protocolo"], p["categoria"], p["urgencia"], "| UBS:", p["encaminhamento"][:50] or "-", "| alerta:", p["alerta_inmet"] or "-")
"""),
    md("## 5. Medição de acerto\nA amostra sintética **infla** o resultado (dados e regras foram escritos juntos). A amostra independente, escrita à mão, é a medida honesta."),
    code("""
import csv as _csv
from classificador import classificar
def acerto(rows):
    n = len(rows)
    c = sum(classificar(r["texto"])["categoria"] == r["categoria_real"] for r in rows)
    u = sum(classificar(r["texto"])["urgencia"] == r["urgencia_real"] for r in rows)
    return n, c / n, u / n
indep = list(_csv.DictReader(open(RAIZ / "dados_sinteticos" / "amostra_independente.csv", encoding="utf-8")))
for grupo in ("desenvolvimento", "teste"):
    n, c, u = acerto([r for r in indep if r["grupo"] == grupo])
    print(f"[{grupo}] {n} relatos | categoria {c:.1%} | urgência {u:.1%}")
"""),
    md("## 6. Falhas tratadas\nO robô não pode parar por causa de uma fonte fora do ar. Aqui simulamos o site de UBS e o servidor de e-mail fora do ar."),
    code("""
import logging, coleta_web, notificador
logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(name)s: %(message)s")
config.OFFLINE = False
config.TIMEOUT_S = 1
unidades, origem = coleta_web.coletar_ubs("http://127.0.0.1:9/ubs")   # porta fechada
print("-> UBS:", len(unidades), "unidades, origem:", origem)

config.SMTP_HOST, config.SMTP_PORTA = "127.0.0.1", 9
config.SMTP_USUARIO, config.SMTP_SENHA, config.EMAIL_DESTINO, config.EMAIL_ATIVO = "robo@exemplo.com", "x", "g@exemplo.com", True
ok = notificador.enviar_com_retry("ELB-DEMO-1", 2, 0.1, dados={"urgencia": "alta", "categoria": "alagamento"})
print("-> e-mail enviado?", ok, "(o robô registra e segue)")
config.EMAIL_ATIVO = False
"""),
    md("## 7. Agendamento\nA busca roda a pedido (`agendador.py agora`) ou sozinha às 08:00 e 18:00 (`agendador.py servir`)."),
    code("""
from datetime import datetime
import agendador
horarios = agendador.parse_horarios("08:00,18:00")
t = datetime.now()
for _ in range(3):
    t = agendador.proxima_execucao(t, horarios)
    print("próxima busca:", t.strftime("%d/%m/%Y %H:%M"))
"""),
]

nb = {"cells": CELULAS, "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
                                     "language_info": {"name": "python"}}, "nbformat": 4, "nbformat_minor": 5}

if __name__ == "__main__":
    SAIDA.parent.mkdir(exist_ok=True)
    SAIDA.write_text(json.dumps(nb, ensure_ascii=False, indent=1), encoding="utf-8")
    print("Gerado:", SAIDA)
