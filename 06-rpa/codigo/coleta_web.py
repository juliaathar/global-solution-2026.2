"""Coleta web da lista pública de UBS (BeautifulSoup4 + seletores CSS + XPath com lxml).

Boas práticas: respeita robots.txt, usa User-Agent identificado, timeout e retry com espera.
Se o site estiver fora do ar, bloquear o robô ou mudar o HTML, cai no snapshot local (caminho seguro).
"""
import logging
import re
import time
import urllib.robotparser
from urllib.parse import urlsplit

import requests
from bs4 import BeautifulSoup
from lxml import etree, html as lxml_html

import config

log = logging.getLogger("rpa.coleta_web")


class ErroColeta(Exception):
    pass


def permitido_por_robots(url: str) -> bool:
    """True se o robots.txt permite (ou não existe). Falha ao ler robots = não bloqueia, mas registra."""
    partes = urlsplit(url)
    robots = f"{partes.scheme}://{partes.netloc}/robots.txt"
    try:
        r = requests.get(robots, headers={"User-Agent": config.USER_AGENT}, timeout=config.TIMEOUT_S)
    except requests.RequestException as e:
        log.warning("Não consegui ler %s (%s); seguindo com cautela", robots, e)
        return True
    if r.status_code != 200:
        return True
    rp = urllib.robotparser.RobotFileParser()
    rp.parse(r.text.splitlines())
    return rp.can_fetch(config.USER_AGENT, url)


def baixar(url: str, tentativas=None, espera_base=None) -> str:
    tentativas = tentativas or config.TENTATIVAS
    espera_base = config.ESPERA_BASE_S if espera_base is None else espera_base
    if not permitido_por_robots(url):
        raise ErroColeta(f"robots.txt não permite acessar {url}")
    ultimo = None
    for i in range(1, tentativas + 1):
        try:
            r = requests.get(url, headers={"User-Agent": config.USER_AGENT}, timeout=config.TIMEOUT_S)
            if 400 <= r.status_code < 500 and r.status_code != 408:
                # 403/404/410/429...: o servidor respondeu "não"; repetir não adianta e pode irritar o site
                raise ErroColeta(f"HTTP {r.status_code}: não adianta repetir")
            r.raise_for_status()  # 5xx e 408 são transitórios: seguem para o retry
            r.encoding = r.apparent_encoding if r.encoding in (None, "ISO-8859-1") else r.encoding
            time.sleep(config.ESPERA_ENTRE_REQUISICOES_S)
            return r.text
        except (requests.RequestException, ErroColeta) as e:
            ultimo = e
            log.warning("Download falhou (tentativa %d/%d): %s", i, tentativas, e)
            if isinstance(e, ErroColeta):
                break  # bloqueio não melhora tentando de novo
            if i < tentativas:
                time.sleep(espera_base * 2 ** (i - 1))
    raise ErroColeta(str(ultimo))


def _limpar(t: str) -> str:
    return re.sub(r"\s+", " ", t.replace("\xa0", " ")).strip(" :")


_CAMPOS = re.compile(r"(Endere[çc]o|Telefones?|Hor[áa]rio[^:]*):\s*(.*?)(?=(?:Endere[çc]o|Telefones?|Hor[áa]rio[^:]*):|$)", re.S | re.I)


def _campos(bloco: str) -> dict:
    """Lê 'Rótulo: valor' do texto da unidade, mesmo quando vários rótulos caem no mesmo <p>."""
    out = {"endereco": "", "telefones": "", "horario": ""}
    for rot, valor in _CAMPOS.findall(bloco):
        chave = "endereco" if rot.lower().startswith("endere") else "telefones" if rot.lower().startswith("telef") else "horario"
        out[chave] = _limpar(valor)
    return out


def _eh_titulo(p_texto: str, forte_texto: str) -> bool:
    return forte_texto.upper().startswith("UBS") and ":" not in p_texto


def extrair_css(doc: str) -> list[dict]:
    """CSS: percorre os <p> do bloco; um <p> só com <strong> 'UBS ...' abre a unidade, os demais viram campos."""
    soup = BeautifulSoup(doc, "lxml")
    unidades, regiao, atual, blocos = [], "", None, []
    for p in soup.select(".sec_serv_conteudo_box p"):
        inter = p.select_one("span.intertitulo")
        if inter:
            regiao = _limpar(inter.get_text())
            continue
        forte = p.select_one("strong")
        texto = p.get_text(" ")
        if forte is not None and _eh_titulo(texto, _limpar(forte.get_text())):
            atual = {"nome": _limpar(forte.get_text()), "regiao": regiao}
            blocos.append([])
            unidades.append(atual)
        elif atual is not None:
            blocos[-1].append(texto)
    return [{**u, **_campos(" ".join(b))} for u, b in zip(unidades, blocos)]


def extrair_xpath(doc: str) -> list[dict]:
    """XPath: acha o título por starts-with/contains e lê os irmãos seguintes até o próximo título."""
    tree = lxml_html.fromstring(doc)
    unidades = []
    titulos = "//div[contains(@class,'sec_serv_conteudo_box')]//p[strong[starts-with(normalize-space(.),'UBS')] and not(contains(.,':'))]"
    for t in tree.xpath(titulos):
        regiao = t.xpath("preceding::span[@class='intertitulo'][1]")
        titulo_xp = "strong[starts-with(normalize-space(.),'UBS')] and not(contains(.,':'))"
        # irmãos seguintes que ainda pertencem a esta unidade (mesmo nº de títulos antes) e não são título
        irmaos = t.xpath(f"following-sibling::p[not({titulo_xp}) and count(preceding-sibling::p[{titulo_xp}]) = $n]",
                         n=len(t.xpath(f"preceding-sibling::p[{titulo_xp}]")) + 1)
        bloco = " ".join(p.text_content() for p in irmaos)
        unidades.append({"nome": _limpar(t.text_content()),
                         "regiao": _limpar(regiao[0].text_content()) if regiao else "", **_campos(bloco)})
    return unidades


def coletar_ubs(url=None, extrator=extrair_css) -> tuple[list[dict], str]:
    """Devolve (unidades, origem). origem: 'web' ou 'snapshot'. Nunca levanta por falha de rede."""
    url = url or config.UBS_URL
    doc, origem = None, "snapshot"
    if not config.OFFLINE:
        try:
            doc, origem = baixar(url), "web"
        except ErroColeta as e:
            log.error("Coleta web falhou (%s); usando snapshot local", e)
    if doc is None:
        doc = config.UBS_SNAPSHOT.read_text(encoding="utf-8")
    unidades = extrator(doc)
    if not unidades and origem == "web":
        log.error("Seletores não encontraram UBS (HTML pode ter mudado); usando snapshot local")
        unidades, origem = extrator(config.UBS_SNAPSHOT.read_text(encoding="utf-8")), "snapshot"
    log.info("UBS coletadas: %d (origem: %s)", len(unidades), origem)
    return unidades, origem


def sugerir_ubs(texto: str, unidades: list[dict]) -> dict | None:
    """Escolhe a UBS que o texto cita. 1º: nome do bairro/unidade inteiro dentro do texto (o mais longo vence);
    2º: palavras do nome ou do endereço em comum (só palavras com 4+ letras e não genéricas). None se nada combinar."""
    from deduplicacao import normalizar
    norm = normalizar(texto)
    por_nome = [(len(n), u) for u in unidades
                if (n := normalizar(u["nome"]).removeprefix("ubs ").strip()) and re.search(rf"\b{re.escape(n)}\b", norm)]
    if por_nome:
        return max(por_nome, key=lambda x: x[0])[1]
    ignorar = {"ubs", "rua", "avenida", "estrada", "praca", "travessa", "esquina", "jardim", "vila", "parque",
               "sao", "jose", "campos", "regiao", "unidades", "avancadas", "onde", "fica", "mais", "proxima",
               "como", "para", "perto", "daqui", "posto", "saude", "pessoal", "consulta", "marcar", "vacina",
               "atendimento", "medico", "gratuito", "preciso", "solucao", "favor", "enviem", "alguem"}
    t = {w for w in norm.split() if len(w) >= 4} - ignorar
    melhor, pontos = None, 0
    for u in unidades:
        chaves = {w for w in normalizar(f"{u['nome']} {u['endereco']}").split() if len(w) >= 4} - ignorar
        n = len(t & chaves)
        if n > pontos:
            melhor, pontos = u, n
    return melhor
