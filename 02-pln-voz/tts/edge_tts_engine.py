"""TTS com edge-tts (nuvem, voz sintética pronta pt-BR). Sem clonagem de voz."""
import asyncio


class EdgeTTS:
    nome = "edge-tts"
    extensao = ".mp3"

    def __init__(self, voz: str = "pt-BR-FranciscaNeural"):
        self.voz = voz

    def sintetizar(self, texto: str, caminho_saida: str) -> str:
        import edge_tts
        asyncio.run(edge_tts.Communicate(texto, self.voz).save(caminho_saida))
        return caminho_saida
