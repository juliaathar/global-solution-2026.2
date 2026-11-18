"""STT com faster-whisper (local, português). Compare 'base' e 'small'."""
import os

from config import APAGAR_AUDIO_APOS_STT


class WhisperSTT:
    def __init__(self, modelo: str = "small", device: str = "cpu", compute_type: str = "int8",
                 apagar_audio: bool | None = None):
        """`apagar_audio=False` só deve ser usado pelos scripts de teste, com áudios do próprio grupo."""
        from faster_whisper import WhisperModel  # import tardio: só quando usado
        self.nome = f"faster-whisper-{modelo}"
        self.apagar_audio = APAGAR_AUDIO_APOS_STT if apagar_audio is None else apagar_audio
        self._modelo = WhisperModel(modelo, device=device, compute_type=compute_type)

    def transcrever(self, caminho_audio: str) -> str:
        try:
            segmentos, _ = self._modelo.transcribe(caminho_audio, language="pt", vad_filter=True)
            return " ".join(s.text.strip() for s in segmentos).strip()
        finally:
            # Retenção mínima (LGPD): não guardar o áudio depois da transcrição.
            if self.apagar_audio and os.path.exists(caminho_audio):
                os.remove(caminho_audio)
