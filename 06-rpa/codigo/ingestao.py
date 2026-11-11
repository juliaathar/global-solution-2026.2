import csv
import logging
from pathlib import Path

log = logging.getLogger("rpa.ingestao")


def ler_relatos(caminho: Path) -> list[dict]:
    """Lê o CSV de relatos. Arquivo ausente ou ilegível devolve lista vazia, com log."""
    try:
        with open(caminho, newline="", encoding="utf-8") as f:
            return list(csv.DictReader(f))
    except FileNotFoundError:
        log.error("Arquivo de entrada ausente: %s", caminho)
    except (OSError, UnicodeDecodeError, csv.Error) as e:
        log.error("Falha ao ler %s: %s", caminho, e)
    return []
