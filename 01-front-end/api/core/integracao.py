"""Importa código das outras disciplinas sem colisão de nomes.

As pastas 02, 04 e 06 têm, cada uma, um módulo chamado `config.py`. Se todas entrassem no sys.path ao
mesmo tempo, o primeiro `import config` venceria e os outros módulos leriam a configuração errada.
`importar_isolado` coloca uma pasta na frente do sys.path só durante o import e depois devolve ao
sys.modules o que estava lá. O módulo importado guarda a referência ao próprio `config`, então continua
funcionando.
"""
import importlib
import sys
from pathlib import Path

from api.core.config import RAIZ_REPO

PASTAS = {
    "voz": RAIZ_REPO / "02-pln-voz",
    "rag": RAIZ_REPO / "03-generative-ai",
    "visao": RAIZ_REPO / "04-visao-computacional" / "codigo",
    "rpa": RAIZ_REPO / "06-rpa" / "codigo",
}
NOMES_EM_CONFLITO = ("config",)


def importar_isolado(pasta: str, modulo: str):
    caminho = str(PASTAS[pasta])
    guardados = {n: sys.modules.pop(n) for n in NOMES_EM_CONFLITO if n in sys.modules}
    sys.path.insert(0, caminho)
    try:
        return importlib.import_module(modulo)
    finally:
        sys.path.remove(caminho)
        for n in NOMES_EM_CONFLITO:
            sys.modules.pop(n, None)
        sys.modules.update(guardados)


def pasta(nome: str) -> Path:
    return PASTAS[nome]
