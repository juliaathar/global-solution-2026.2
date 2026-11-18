"""Prepara o texto do LLM para o TTS: sem markdown e emoji, frases curtas,
números, siglas, valores, datas e horas escritos como se fala."""
import re

from .extenso import numero_por_extenso

MESES = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho",
         "agosto", "setembro", "outubro", "novembro", "dezembro"]

# Soletradas letra a letra. Siglas lidas como palavra (SUS, SAMU, CRAS) ganham grafia fonética.
SIGLAS = {
    "UBS": "U B S", "UPA": "U P A", "CPF": "C P F", "RG": "R G", "CEP": "C E P",
    "INSS": "I N S S", "BO": "B O", "CNH": "C N H", "CRAS": "crás", "CREAS": "crêas",
    "SUS": "sus", "SAMU": "samu", "FIAP": "fiap", "ODS": "O D S",
}

# Telefones de emergência e serviços são falados dígito a dígito.
TELEFONES_CURTOS = {"153", "156", "180", "188", "190", "192", "193", "197"}

_DIGITOS = ["zero", "um", "dois", "três", "quatro", "cinco", "seis", "sete", "oito", "nove"]

MAX_PALAVRAS_FRASE = 18

_EMOJI = re.compile(
    "[\U0001F000-\U0001FAFF\U00002600-\U000027BF\U0001F1E6-\U0001F1FF\U00002B00-\U00002BFF️‍]+")


def limpar_markdown(texto: str) -> str:
    texto = re.sub(r"```.*?```", " ", texto, flags=re.S)
    texto = re.sub(r"`([^`]*)`", r"\1", texto)
    texto = re.sub(r"!\[[^\]]*\]\([^)]*\)", " ", texto)
    texto = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", texto)       # [texto](url) -> texto
    texto = re.sub(r"https?://\S+", " ", texto)
    texto = re.sub(r"^\s{0,3}#{1,6}\s*", "", texto, flags=re.M)  # títulos
    texto = re.sub(r"^\s*[-*•]\s+", "", texto, flags=re.M)        # marcadores
    texto = re.sub(r"^\s*\d+[.)]\s+", "", texto, flags=re.M)      # listas numeradas
    texto = re.sub(r"(\*\*|__|\*|_|~~)", "", texto)
    texto = _EMOJI.sub("", texto)
    return texto


def _data(m: re.Match) -> str:
    dia, mes, ano = int(m.group(1)), int(m.group(2)), m.group(3)
    if not 1 <= mes <= 12 or not 1 <= dia <= 31:
        return m.group(0)
    d = "primeiro" if dia == 1 else numero_por_extenso(dia)
    texto = f"{d} de {MESES[mes - 1]}"
    if ano:
        a = int(ano) + (2000 if len(ano) == 2 else 0)
        texto += f" de {numero_por_extenso(a)}"
    return texto


def _moeda(m: re.Match) -> str:
    reais = int(m.group(1).replace(".", ""))
    centavos = int(m.group(2)) if m.group(2) else 0
    partes = []
    if reais or not centavos:
        partes.append(f"{numero_por_extenso(reais)} {'real' if reais == 1 else 'reais'}")
    if centavos:
        partes.append(f"{numero_por_extenso(centavos)} {'centavo' if centavos == 1 else 'centavos'}")
    return " e ".join(partes)


def _hora(m: re.Match) -> str:
    h, mi = int(m.group(1)), int(m.group(2) or 0)
    if h > 24 or mi > 59:
        return m.group(0)
    texto = f"{numero_por_extenso(h, feminino=True)} {'hora' if h == 1 else 'horas'}"
    if mi:
        texto += f" e {numero_por_extenso(mi)} {'minuto' if mi == 1 else 'minutos'}"
    return texto


def _decimal(m: re.Match) -> str:
    inteiro, frac = m.group(1).replace(".", ""), m.group(2)
    return f"{numero_por_extenso(int(inteiro))} vírgula {' '.join(_DIGITOS[int(c)] for c in frac)}"


def _inteiro(m: re.Match) -> str:
    bruto = m.group(0)
    if bruto in TELEFONES_CURTOS:
        return " ".join(_DIGITOS[int(c)] for c in bruto)
    n = int(bruto.replace(".", ""))
    if n > 999_999_999:  # número muito longo (telefone, protocolo): dígito a dígito
        return " ".join(_DIGITOS[int(c)] for c in bruto if c.isdigit())
    return numero_por_extenso(n)


def _siglas(texto: str) -> str:
    for sigla, fala in SIGLAS.items():
        texto = re.sub(rf"\b{sigla}\b", fala, texto)
    return texto


def _quebrar_frases(texto: str) -> str:
    saida = []
    for frase in re.split(r"(?<=[.!?])\s+", texto.strip()):
        palavras = frase.split()
        if len(palavras) > MAX_PALAVRAS_FRASE and "," in frase:
            # quebra na vírgula mais próxima do meio
            pos = [m.start() for m in re.finditer(",", frase)]
            meio = len(frase) / 2
            corte = min(pos, key=lambda p: abs(p - meio))
            esq, dir_ = frase[:corte].strip(), frase[corte + 1:].strip()
            if len(esq.split()) >= 5 and len(dir_.split()) >= 5:
                dir_ = dir_[0].upper() + dir_[1:]
                saida += [esq + ".", dir_]
                continue
        saida.append(frase)
    return " ".join(saida)


def adaptar_para_fala(texto: str) -> str:
    t = limpar_markdown(texto)
    t = re.sub(r"\b(\d{1,2})/(\d{1,2})(?:/(\d{4}|\d{2}))?\b", _data, t)
    t = re.sub(r"R\$\s*(\d{1,3}(?:\.\d{3})*|\d+)(?:,(\d{1,2}))?", _moeda, t)
    t = re.sub(r"\b(\d{1,2})\s*h(?:(\d{2}))?\b", _hora, t)
    t = re.sub(r"\b(\d{1,2}):(\d{2})\b", _hora, t)
    t = re.sub(r"(\d+(?:\.\d{3})*(?:,\d+)?)\s*%", lambda m: m.group(1) + " por cento", t)
    t = re.sub(r"\b(\d{1,3}(?:\.\d{3})*),(\d+)\b", _decimal, t)
    t = re.sub(r"\b\d{1,3}(?:\.\d{3})+\b|\b\d+\b", _inteiro, t)
    t = _siglas(t)
    t = re.sub(r"\s*[\n\r]+\s*", ". ", t)
    t = re.sub(r"\.\s*\.", ".", t)
    t = re.sub(r"[ \t]+", " ", t).strip()
    return _quebrar_frases(t)
