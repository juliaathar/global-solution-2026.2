"""Webcrawler do Arquivo de Notícias da Prefeitura de São José dos Campos.

Percorre as páginas `?pag=N` (limite e espera configuráveis), extrai cartões com CSS e o id da notícia com XPath,
filtra por palavras-chave de zeladoria e saúde e devolve "relatos públicos" para o pipeline.
Não usa o formulário de busca (tem reCAPTCHA). Se uma página falhar, mantém o que já coletou;
sem nenhuma página, usa os snapshots locais.
"""
import logging
import re
import unicodedata

from bs4 import BeautifulSoup
from lxml import html as lxml_html

import config
from coleta_web import ErroColeta, baixar

log = logging.getLogger("rpa.noticias")


def extrair_css(doc: str) -> list[dict]:
    """CSS: cada `div.noticia-02 a` traz a data em `h6` e o título em `h5`."""
    soup = BeautifulSoup(doc, "lxml")
    noticias = []
    for a in soup.select("div.noticia-02 a[href*='noticia_id']"):
        m = re.search(r"noticia_id=(\d+)", a["href"])
        if m and a.select_one("h5"):
            noticias.append({"noticia_id": m.group(1), "data": a.select_one("h6").get_text(strip=True) if a.select_one("h6") else "",
                             "titulo": a.select_one("h5").get_text(" ", strip=True)})
    return noticias


def extrair_xpath(doc: str) -> list[dict]:
    """XPath: mesmo resultado, localizando o link por `contains(@href, 'noticia_id')`."""
    tree = lxml_html.fromstring(doc)
    noticias = []
    for a in tree.xpath("//div[@class='noticia-02']//a[contains(@href,'noticia_id=') and h5]"):
        noticias.append({"noticia_id": a.get("href").split("noticia_id=")[1],
                         "data": " ".join(a.xpath("string(h6)").split()),
                         "titulo": " ".join(a.xpath("string(h5)").split())})
    return noticias


def _sem_acento(t: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", t.lower()) if unicodedata.category(c) != "Mn")


def filtrar_por_tema(noticias: list[dict], palavras=None) -> list[dict]:
    palavras = [_sem_acento(p) for p in (palavras or config.PALAVRAS_NOTICIA)]
    return [n for n in noticias if any(p in _sem_acento(n["titulo"]) for p in palavras)]


def rastrear(max_paginas=None, url=None, baixar_fn=baixar) -> tuple[list[dict], dict]:
    """Percorre as páginas do arquivo. Devolve (notícias, info) com info = {paginas, origem, falhas}."""
    max_paginas = max_paginas or config.MAX_PAGINAS
    url = url or config.NOTICIAS_URL
    todas, vistos, info = [], set(), {"paginas": 0, "origem": "web", "falhas": 0}
    if config.OFFLINE:
        max_paginas = 0
    for pag in range(1, max_paginas + 1):
        try:
            doc = baixar_fn(f"{url}?pag={pag}&dat=")
        except ErroColeta as e:
            info["falhas"] += 1
            log.error("Página %d do arquivo falhou (%s); mantendo as %d já coletadas", pag, e, info["paginas"])
            break
        novas = [n for n in extrair_css(doc) if n["noticia_id"] not in vistos]
        if not novas:
            log.warning("Página %d sem notícias novas (fim do arquivo ou HTML mudou); parando", pag)
            break
        vistos.update(n["noticia_id"] for n in novas)
        todas += novas
        info["paginas"] += 1
    if not todas:
        info["origem"] = "snapshot"
        log.error("Nenhuma página coletada; usando snapshots locais")
        for arq in config.NOTICIAS_SNAPSHOTS:
            todas += extrair_css(arq.read_text(encoding="utf-8", errors="replace"))
        info["paginas"] = len(config.NOTICIAS_SNAPSHOTS)
    log.info("Crawler: %d notícias em %d páginas (origem: %s)", len(todas), info["paginas"], info["origem"])
    return todas, info


def coletar_relatos_publicos(max_paginas=None) -> tuple[list[dict], dict]:
    """Notícias de interesse como relatos para o pipeline (id 'N<noticia_id>', texto = data e título)."""
    noticias, info = rastrear(max_paginas)
    escolhidas = filtrar_por_tema(noticias)
    relatos = [{"id": f"N{n['noticia_id']}", "texto": f"{n['titulo']} ({n['data']})",
                "categoria_real": "", "urgencia_real": "", "origem": "noticia_publica"} for n in escolhidas]
    info["total"], info["relevantes"] = len(noticias), len(relatos)
    return relatos, info
