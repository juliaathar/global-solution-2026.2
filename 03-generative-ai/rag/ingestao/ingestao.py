"""Ingestão do corpus do motor RAG do EloBairro.

Lê corpus/fontes_entrada.csv (url, categoria), baixa cada página pública da Prefeitura de
São José dos Campos, limpa o texto e grava:
  - corpus/bruto/<id>.html        HTML original (reprodutibilidade)
  - corpus/documentos.jsonl       um documento por linha, com metadados
  - corpus/fontes.csv             URL, data de consulta, título, status e hash de cada fonte

Boas práticas: respeita robots.txt, User-Agent identificado, espera entre requisições,
timeout e retry. Se o download falhar mas existir HTML em corpus/bruto/, usa o arquivo local.

Uso (a partir de 03-generative-ai):  python rag/ingestao/ingestao.py [--offline]
"""
import argparse
import csv
import hashlib
import json
import logging
import re
import time
import urllib.robotparser
from datetime import date
from pathlib import Path
from urllib.parse import urlsplit

import requests
from bs4 import BeautifulSoup

RAIZ = Path(__file__).resolve().parents[2]
CORPUS = RAIZ / "corpus"
BRUTO = CORPUS / "bruto"
USER_AGENT = "EloBairro-Academico/1.0 (projeto FIAP Global Solution; uso didatico)"
TIMEOUT_S = 20
ESPERA_S = 1.5
TENTATIVAS = 3
MIN_CARACTERES = 200  # abaixo disso a página é considerada vazia

# botões de cartão e aviso de cookies: não têm informação de serviço
RUIDO = re.compile(r"^(informações|serviço|acessar|saiba mais|a prefeitura de são josé dos campos utiliza cookies)\b", re.I)

log = logging.getLogger("rag.ingestao")


def doc_id(url: str) -> str:
    """Identificador estável derivado do caminho da URL."""
    caminho = urlsplit(url).path.strip("/")
    caminho = caminho.removeprefix("servicos/")
    return re.sub(r"[^a-z0-9]+", "-", caminho.lower()).strip("-")


def permitido_por_robots(url: str, cache: dict) -> bool:
    p = urlsplit(url)
    origem = f"{p.scheme}://{p.netloc}"
    if origem not in cache:
        rp = urllib.robotparser.RobotFileParser()
        try:
            r = requests.get(f"{origem}/robots.txt", headers={"User-Agent": USER_AGENT}, timeout=TIMEOUT_S)
            rp.parse(r.text.splitlines() if r.status_code == 200 else [])  # sem robots = permitido
        except requests.RequestException as e:
            log.warning("robots.txt ilegível (%s); seguindo com cautela", e)
            rp.parse([])
        cache[origem] = rp
    return cache[origem].can_fetch(USER_AGENT, url)


def baixar(url: str) -> str:
    ultimo = None
    for i in range(TENTATIVAS):
        try:
            r = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=TIMEOUT_S)
            if r.status_code == 200:
                r.encoding = r.apparent_encoding if not r.encoding or r.encoding.lower() == "iso-8859-1" else r.encoding
                return r.text
            ultimo = f"HTTP {r.status_code}"
        except requests.RequestException as e:
            ultimo = str(e)
        time.sleep(2 ** i)
    raise RuntimeError(ultimo)


def limpar(html: str) -> tuple[str, str]:
    """Devolve (titulo, texto). Mantém títulos de seção como linhas '## ...' para o chunking por estrutura."""
    soup = BeautifulSoup(html, "lxml")
    og = soup.find("meta", property="og:title")
    titulo = (og.get("content") if og and og.get("content") else (soup.title.string if soup.title else "")).strip()
    titulo = re.sub(r"\s*-\s*Prefeitura de São José dos Campos\s*$", "", titulo)
    area = soup.select_one("div.sec_serv_conteudo") or soup.body
    for t in area.select("script, style, nav, form, noscript, iframe, button"):
        t.decompose()
    linhas = []
    for el in area.find_all(["h1", "h2", "h3", "h4", "p", "li", "td", "th"]):
        # evita duplicar: pega só o texto "folha" de cada elemento
        if el.find(["p", "li", "h1", "h2", "h3", "h4"]) and el.name in ("li",):
            continue
        txt = re.sub(r"\s+", " ", el.get_text(" ", strip=True)).strip()
        if not txt:
            continue
        if RUIDO.match(txt):
            continue
        linhas.append(f"## {txt}" if el.name in ("h1", "h2", "h3", "h4") else txt)
    # remove linhas repetidas consecutivas
    saida = [l for i, l in enumerate(linhas) if i == 0 or l != linhas[i - 1]]
    return titulo, "\n".join(saida)


def main(offline: bool = False) -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    BRUTO.mkdir(parents=True, exist_ok=True)
    with open(CORPUS / "fontes_entrada.csv", encoding="utf-8", newline="") as f:
        entradas = list(csv.DictReader(f))

    robots, docs, fontes = {}, [], []
    hoje = date.today().isoformat()
    for e in entradas:
        url, cat = e["url"], e["categoria"]
        did = doc_id(url)
        arq = BRUTO / f"{did}.html"
        status, html = "ok", None
        try:
            if offline:
                raise RuntimeError("modo offline")
            if not permitido_por_robots(url, robots):
                status = "bloqueado_por_robots"
            else:
                html = baixar(url)
                arq.write_text(html, encoding="utf-8")
                time.sleep(ESPERA_S)
        except RuntimeError as err:
            if arq.exists():
                html, status = arq.read_text(encoding="utf-8"), "ok_cache_local"
                log.warning("%s: usando cache local (%s)", did, err)
            else:
                status = f"falha: {err}"
        titulo, texto = ("", "")
        if html:
            titulo, texto = limpar(html)
            if len(texto) < MIN_CARACTERES:
                status = "descartado_texto_curto"
        if status.startswith("ok"):
            docs.append({"id": did, "url": url, "titulo": titulo, "categoria": cat,
                         "data_consulta": hoje, "texto": texto})
        log.info("%-60s %-22s %6d chars", did, status, len(texto))
        fontes.append({"id": did, "url": url, "titulo": titulo, "categoria": cat, "data_consulta": hoje,
                       "status": status, "n_caracteres": len(texto),
                       "sha256": hashlib.sha256(texto.encode()).hexdigest()[:16] if texto else ""})

    with open(CORPUS / "documentos.jsonl", "w", encoding="utf-8") as f:
        for d in docs:
            f.write(json.dumps(d, ensure_ascii=False) + "\n")
    with open(CORPUS / "fontes.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(fontes[0]))
        w.writeheader()
        w.writerows(fontes)
    log.info("%d documentos aproveitados de %d fontes", len(docs), len(entradas))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--offline", action="store_true", help="usa só o HTML já salvo em corpus/bruto")
    main(ap.parse_args().offline)
