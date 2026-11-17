"""Configuração do robô RPA. Valores podem ser sobrescritos por variáveis de ambiente."""
import os
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent


def _carregar_env(caminho: Path) -> None:
    """Lê KEY=VALOR de um .env (sem dependências). Variáveis já definidas no ambiente têm prioridade."""
    if not caminho.is_file():
        return
    for linha in caminho.read_text(encoding="utf-8").splitlines():
        linha = linha.strip()
        if linha and not linha.startswith("#") and "=" in linha:
            chave, valor = linha.split("=", 1)
            os.environ.setdefault(chave.strip(), valor.split(" #")[0].strip().strip('"').strip("'"))


_carregar_env(RAIZ / ".env")  # 06-rpa/.env, fora do git
ENTRADA = Path(os.getenv("RPA_ENTRADA", RAIZ / "dados_sinteticos" / "relatos.csv"))
SAIDA = Path(os.getenv("RPA_SAIDA", RAIZ / "saida"))
BANCO = SAIDA / "protocolos.db"
LOG = SAIDA / "execucao.log"
RELATORIO = SAIDA / "relatorio_execucao.json"
REVISAO = SAIDA / "revisao_humana.csv"

CONFIANCA_MINIMA = float(os.getenv("RPA_CONFIANCA_MINIMA", "0.5"))
SIMILARIDADE_DUPLICADO = float(os.getenv("RPA_SIMILARIDADE", "0.85"))
TENTATIVAS = int(os.getenv("RPA_TENTATIVAS", "3"))
ESPERA_BASE_S = float(os.getenv("RPA_ESPERA_BASE", "0.2"))
TAMANHO_MIN, TAMANHO_MAX = 10, 500
API_URL = os.getenv("RPA_API_URL", "")  # vazio = notificação simulada
TIMEOUT_S = float(os.getenv("RPA_TIMEOUT", "5"))

# Coleta web (lista pública de UBS). RPA_OFFLINE=1 usa só o snapshot local.
UBS_URL = os.getenv("RPA_UBS_URL", "https://www.sjc.sp.gov.br/servicos/saude/unidades-basicas-de-saude-ubs/unidades-basicas-de-saude/")
UBS_SNAPSHOT = RAIZ / "dados_sinteticos" / "ubs_sjc_snapshot.html"
OFFLINE = os.getenv("RPA_OFFLINE", "") == "1"
USER_AGENT = "EloBairro-RPA/1.0 (projeto academico FIAP; contato: ver README)"
ESPERA_ENTRE_REQUISICOES_S = float(os.getenv("RPA_ESPERA_REQ", "1"))

# Alertas Inmet (RSS) e crawler do Arquivo de Notícias de SJC
INMET_URL = os.getenv("RPA_INMET_URL", "https://apiprevmet3.inmet.gov.br/avisos/rss")
INMET_SNAPSHOT = RAIZ / "dados_sinteticos" / "inmet_avisos_snapshot.xml"
INMET_AREA = os.getenv("RPA_INMET_AREA", "Vale do Paraíba Paulista")  # mesorregião de São José dos Campos
INMET_EVENTOS = ("Tempestade", "Chuvas Intensas", "Acumulado de Chuva", "Vendaval")
NOTICIAS_URL = "https://servicos.sjc.sp.gov.br/arquivonoticias/arquivo_noticias.aspx"
NOTICIAS_SNAPSHOTS = [RAIZ / "dados_sinteticos" / "arquivo_noticias_pag1.html",
                      RAIZ / "dados_sinteticos" / "arquivo_noticias_pag2.html"]
USAR_NOTICIAS = os.getenv("RPA_USAR_NOTICIAS", "") == "1"  # liga o crawler como fonte extra de relatos
MAX_PAGINAS = int(os.getenv("RPA_MAX_PAGINAS", "3"))
PALAVRAS_NOTICIA = ("buraco", "tapa-buraco", "alagamento", "enchente", "bueiro", "iluminação", "iluminacao",
                    "lixo", "entulho", "calçada", "calcada", "chuva", "ubs", "posto de saúde")

# Canal de e-mail (SMTP). Desligado se usuário, senha ou destino faltarem. A senha vem só do ambiente.
SMTP_HOST = os.getenv("RPA_SMTP_HOST", "smtp.gmail.com")
SMTP_PORTA = int(os.getenv("RPA_SMTP_PORTA", "587"))
SMTP_USUARIO = os.getenv("RPA_SMTP_USUARIO", "")
SMTP_SENHA = os.getenv("RPA_SMTP_SENHA", "")
EMAIL_DESTINO = os.getenv("RPA_EMAIL_DESTINO", "")
EMAIL_URGENCIAS = tuple(os.getenv("RPA_EMAIL_URGENCIAS", "alta").split(","))  # só estas urgências geram e-mail
EMAIL_ATIVO = bool(SMTP_USUARIO and SMTP_SENHA and EMAIL_DESTINO)

# Agendamento: horários diários da busca automática (HH:MM, separados por vírgula). Padrão: duas vezes ao dia.
HORARIOS = os.getenv("RPA_HORARIOS", "08:00,18:00")
HISTORICO = SAIDA / "historico_execucoes.jsonl"
LOCK = SAIDA / "agendador.lock"
LOCK_VALIDADE_S = int(os.getenv("RPA_LOCK_VALIDADE", "3600"))  # lock mais velho que isso é considerado esquecido
