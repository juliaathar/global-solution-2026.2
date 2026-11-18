"""TTS com Piper (local). Baixe uma voz pt-BR, por exemplo pt_BR-faber-medium."""
import wave


class PiperTTS:
    nome = "piper"
    extensao = ".wav"

    def __init__(self, caminho_modelo: str = "pt_BR-faber-medium.onnx"):
        from piper import PiperVoice
        self._voz = PiperVoice.load(caminho_modelo)

    def sintetizar(self, texto: str, caminho_saida: str) -> str:
        with wave.open(caminho_saida, "wb") as wav:
            self._voz.synthesize_wav(texto, wav)
        return caminho_saida
