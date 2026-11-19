"""Configuração lida do .env (veja .env.example na raiz do repositório)."""
import os
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parents[1] / ".env")
except ImportError:  # python-dotenv é opcional
    pass

STT_MODEL = os.getenv("STT_MODEL", "small")        # base | small
TTS_ENGINE = os.getenv("TTS_ENGINE", "piper")       # piper (escolhido, local) | edge-tts (nuvem)
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama")  # ollama | openai | gemini | groq
LLM_MODEL = os.getenv("LLM_MODEL", "qwen2.5:1.5b")  # escolhido: empata em qualidade com o 3b e leva metade do tempo
LLM_API_KEY = os.getenv("LLM_API_KEY", "")

# Cuidado com LGPD: o áudio enviado ao STT é apagado logo após a transcrição.
APAGAR_AUDIO_APOS_STT = True
# Provedores em nuvem exigem avisar o usuário.
USA_NUVEM = LLM_PROVIDER in ("openai", "gemini", "groq") or TTS_ENGINE == "edge-tts"

SAIDA_DIR = Path(__file__).resolve().parent / "saida"
