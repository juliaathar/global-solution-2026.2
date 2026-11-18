"""Números por extenso em português do Brasil (0 a 999.999.999)."""

_UNIDADES = ["zero", "um", "dois", "três", "quatro", "cinco", "seis", "sete", "oito", "nove", "dez",
             "onze", "doze", "treze", "catorze", "quinze", "dezesseis", "dezessete", "dezoito", "dezenove"]
_DEZENAS = ["", "", "vinte", "trinta", "quarenta", "cinquenta", "sessenta", "setenta", "oitenta", "noventa"]
_CENTENAS = ["", "cento", "duzentos", "trezentos", "quatrocentos", "quinhentos",
             "seiscentos", "setecentos", "oitocentos", "novecentos"]


def _ate_999(n: int) -> str:
    if n == 100:
        return "cem"
    partes = []
    c, resto = divmod(n, 100)
    if c:
        partes.append(_CENTENAS[c])
    if resto:
        if resto < 20:
            partes.append(_UNIDADES[resto])
        else:
            d, u = divmod(resto, 10)
            partes.append(_DEZENAS[d] + (f" e {_UNIDADES[u]}" if u else ""))
    return " e ".join(partes)


def _juntar(esq: str, resto: int, texto_resto: str) -> str:
    """'e' antes do último bloco se ele for < 100 ou centena redonda; senão só espaço."""
    if resto == 0:
        return esq
    sep = " e " if resto < 100 or resto % 100 == 0 else " "
    return f"{esq}{sep}{texto_resto}"


def numero_por_extenso(n: int, feminino: bool = False) -> str:
    if n < 0 or n > 999_999_999:
        raise ValueError("fora do intervalo suportado")
    if n == 0:
        return "zero"
    milhoes, resto = divmod(n, 1_000_000)
    milhares, centenas = divmod(resto, 1000)
    texto = ""
    if milhoes:
        texto = "um milhão" if milhoes == 1 else f"{_ate_999(milhoes)} milhões"
    if milhares:
        mil = "mil" if milhares == 1 else f"{_ate_999(milhares)} mil"
        texto = _juntar(texto, milhares, mil) if texto else mil
        # o resto depois de milhões só ganha "e" se o último bloco for simples
    if centenas:
        bloco = _ate_999(centenas)
        texto = _juntar(texto, centenas, bloco) if texto else bloco
    if feminino:
        texto = _feminino(texto)
    return texto


def _feminino(texto: str) -> str:
    palavras = texto.split(" ")
    if palavras[-1] == "um":
        palavras[-1] = "uma"
    elif palavras[-1] == "dois":
        palavras[-1] = "duas"
    return " ".join(palavras)
