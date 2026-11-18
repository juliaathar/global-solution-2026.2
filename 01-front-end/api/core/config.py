"""Configuração da API, lida do ambiente e do .env da raiz (nunca versionado).

Valores sensíveis (chaves de LLM, token do IoT) vêm só do ambiente. Nada aqui tem chave embutida.
"""
import os
from pathlib import Path

RAIZ_REPO = Path(__file__).resolve().parents[3]
RAIZ_FRONT = RAIZ_REPO / "01-front-end"


def _carregar_env(arquivo: Path) -> None:
    """KEY=VALOR por linha; comentários com #. Variáveis já definidas no ambiente têm prioridade."""
    if not arquivo.is_file():
        return
    for linha in arquivo.read_text(encoding="utf-8").splitlines():
        linha = linha.split("#", 1)[0].strip()
        if "=" in linha:
            chave, valor = linha.split("=", 1)
            os.environ.setdefault(chave.strip(), valor.strip().strip('"').strip("'"))


_carregar_env(RAIZ_REPO / ".env")

# CORS: só as origens listadas (o Streamlit local, por padrão). Nunca "*".
ALLOWED_ORIGINS = [o.strip() for o in os.getenv("ALLOWED_ORIGINS", "http://localhost:8501").split(",") if o.strip()]

# LLM (mesmas variáveis usadas pelo RAG da pasta 03)
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "extrativo").lower()
LLM_MODEL = os.getenv("LLM_MODEL", "")
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
LLM_TIMEOUT_S = float(os.getenv("LLM_TIMEOUT_S", "20"))

# Banco da API (ocorrências e eventos IoT). O banco de protocolos é o mesmo do robô RPA (pasta 06).
DADOS_DIR = Path(os.getenv("ELB_DADOS", RAIZ_FRONT / "dados"))
BANCO_APP = DADOS_DIR / "elobairro.db"
BANCO_PROTOCOLOS_RPA = Path(os.getenv("RPA_BANCO", RAIZ_REPO / "06-rpa" / "saida" / "protocolos.db"))
RELATORIO_RPA = [RAIZ_REPO / "06-rpa" / "saida" / "relatorio_execucao.json",
                 RAIZ_REPO / "06-rpa" / "evidencias" / "relatorio_execucao.json"]

# Mesmos limites de texto do robô RPA (06-rpa/codigo/config.py)
TEXTO_MIN, TEXTO_MAX = 10, 500
SIMILARIDADE_DUPLICADO = float(os.getenv("RPA_SIMILARIDADE", "0.85"))
CONFIANCA_REVISAO = 0.7  # abaixo disso o relato vai para revisão de uma pessoa

# IoT (pasta 05): eventos abaixo do limiar ou da classe "ambiente" não viram alerta
IOT_LIMIAR = float(os.getenv("IOT_LIMIAR", "0.80"))
IOT_TOKEN = os.getenv("IOT_TOKEN", "")  # se definido, a ponte do IoT precisa mandar o cabeçalho X-Dispositivo-Token
