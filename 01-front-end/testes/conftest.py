"""Configuração dos testes: bancos temporários e nenhum LLM real (nada sai da máquina)."""
import os
import sys
import tempfile
from pathlib import Path

_TMP = tempfile.mkdtemp(prefix="elobairro_testes_")
os.environ["ELB_DADOS"] = _TMP
os.environ["RPA_BANCO"] = str(Path(_TMP) / "protocolos.db")
os.environ["LLM_PROVIDER"] = "extrativo"
os.environ["IOT_TOKEN"] = ""
os.environ["ALLOWED_ORIGINS"] = "http://localhost:8501"
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
