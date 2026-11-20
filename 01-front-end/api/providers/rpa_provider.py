"""Liga a API ao robô RPA (pasta 06): mesma máscara de dados pessoais, mesmo classificador,
mesma deduplicação e o MESMO banco de protocolos. Assim, um protocolo aberto pelo app e um aberto
pelo robô seguem a mesma numeração e o robô nunca reabre o que o app já registrou.
"""
import json
from functools import lru_cache
from pathlib import Path

from api.core import config
from api.core.integracao import importar_isolado


@lru_cache(maxsize=1)
def _modulos():
    privacidade = importar_isolado("rpa", "privacidade")
    deduplicacao = importar_isolado("rpa", "deduplicacao")
    classificador = importar_isolado("rpa", "classificador")
    armazenamento = importar_isolado("rpa", "armazenamento")
    return privacidade, deduplicacao, classificador, armazenamento


def mascarar(texto: str) -> tuple[str, int]:
    return _modulos()[0].mascarar(texto)


def classificar(texto: str) -> dict:
    return _modulos()[2].classificar(texto)


def similaridade(a: str, b: str) -> float:
    from difflib import SequenceMatcher
    norm = _modulos()[1].normalizar
    return SequenceMatcher(None, norm(a), norm(b)).ratio()


def gerar_protocolo(relato_id: str, categoria: str, urgencia: str, confianca: float) -> tuple[str, bool]:
    """Grava no banco do robô. Idempotente: o mesmo relato_id devolve o protocolo já existente."""
    banco = _modulos()[3].Armazenamento(config.BANCO_PROTOCOLOS_RPA)
    try:
        linha = banco.con.execute("SELECT protocolo FROM protocolos WHERE relato_id=?", (relato_id,)).fetchone()
        if linha:
            return linha[0], False
        return banco.salvar(relato_id, categoria, urgencia, confianca), True
    finally:
        banco.fechar()


def relatorio_execucao() -> tuple[Path | None, dict]:
    """Último relatório do robô que tenha protocolos: o da saída local, senão o das evidências versionadas.

    Quando o robô roda de novo sobre os mesmos relatos, o relatório novo vem sem protocolos (todos já
    processados). Nesse caso usa o anterior com protocolos, para o painel não ficar vazio.
    """
    vazio: tuple[Path | None, dict] = (None, {})
    for arq in config.RELATORIO_RPA:
        if not arq.is_file():
            continue
        try:
            dados = json.loads(arq.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if dados.get("protocolos"):
            return arq, dados
        if vazio[0] is None:
            vazio = (arq, dados)
    return vazio
