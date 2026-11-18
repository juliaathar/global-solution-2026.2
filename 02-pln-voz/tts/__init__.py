def criar_tts(engine: str):
    """Importa só o motor escolhido, para não exigir as duas dependências."""
    if engine == "piper":
        from .piper_engine import PiperTTS
        return PiperTTS()
    from .edge_tts_engine import EdgeTTS
    return EdgeTTS()
