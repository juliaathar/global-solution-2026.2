"""Configuração do robô RPA. Valores podem ser sobrescritos por variáveis de ambiente."""
import os
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
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
