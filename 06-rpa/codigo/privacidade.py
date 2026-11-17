"""Mascara dados pessoais do texto livre antes de classificar, gravar ou registrar em log.

Cobre CPF, e-mail, telefone brasileiro, CEP e nome dito em primeira pessoa ("me chamo ...").
É uma proteção por padrões: não pega todo dado pessoal (ex.: nome sem apresentação, endereço completo).
"""
import re

PADROES = [
    ("CPF", re.compile(r"(?<!\d)\d{3}\.?\d{3}\.?\d{3}-?\d{2}(?!\d)")),
    ("EMAIL", re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")),
    ("TELEFONE", re.compile(r"(?<!\d)(?:\+?55[\s-]?)?(?:\(?\d{2}\)?[\s-]?)?9?\d{4}[-\s]?\d{4}(?!\d)")),
    ("CEP", re.compile(r"(?<!\d)\d{5}-\d{3}(?!\d)")),
]
NOME = re.compile(r"((?i:me chamo|meu nome é|meu nome e|sou o|sou a)\s+)"
                  r"([A-ZÀ-Ú][\wÀ-ú]+(?:\s+[A-ZÀ-Ú][\wÀ-ú]+){0,2})")


def mascarar(texto: str) -> tuple[str, int]:
    """Devolve (texto mascarado, quantidade de trechos substituídos)."""
    total = 0
    for rotulo, padrao in PADROES:
        texto, n = padrao.subn(f"[{rotulo}]", texto)
        total += n
    texto, n = NOME.subn(r"\1[NOME]", texto)
    return texto, total + n
