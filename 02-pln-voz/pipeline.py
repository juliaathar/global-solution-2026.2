"""Orquestra um turno: áudio -> STT -> LLM+RAG -> adaptação -> TTS, medindo cada etapa.

Latência: `total` vai da chegada do áudio até o áudio da resposta estar pronto. Como o
player só começa a tocar nesse ponto (a síntese não é por streaming), `total` é o tempo
da pergunta até o início da resposta falada, que é o que o enunciado pede.
"""
import csv
import time
import uuid
from pathlib import Path

from adaptacao_fala import adaptar_para_fala
from config import SAIDA_DIR
from interfaces import STT, TTS, ResultadoTurno
from llm import Assistente

MSG_NAO_OUVI = "Não consegui ouvir. Pode repetir, por favor?"
MANTER_AUDIOS = 5  # respostas sintetizadas guardadas na pasta de saída


class PipelineVoz:
    def __init__(self, stt: STT, assistente: Assistente, tts: TTS, log_latencia: Path | None = None):
        self.stt, self.assistente, self.tts = stt, assistente, tts
        self.log_latencia = log_latencia
        SAIDA_DIR.mkdir(exist_ok=True)

    def turno(self, caminho_audio: str) -> ResultadoTurno:
        lat: dict[str, float] = {}
        t0 = time.perf_counter()

        t = time.perf_counter()
        pergunta = self.stt.transcrever(caminho_audio)
        lat["stt"] = time.perf_counter() - t

        t = time.perf_counter()
        if pergunta.strip():
            resposta = self.assistente.perguntar(pergunta)
            motivo = self.assistente.ultimo_motivo
        else:  # silêncio ou ruído: não manda nada ao LLM
            resposta, motivo = MSG_NAO_OUVI, "sem_fala"
        lat["llm_rag"] = time.perf_counter() - t

        t = time.perf_counter()
        fala = adaptar_para_fala(resposta)
        lat["adaptacao"] = time.perf_counter() - t

        t = time.perf_counter()
        saida = str(SAIDA_DIR / f"resp_{uuid.uuid4().hex[:8]}{getattr(self.tts, 'extensao', '.mp3')}")
        self.tts.sintetizar(fala, saida)
        lat["tts"] = time.perf_counter() - t

        lat["total"] = time.perf_counter() - t0
        self._registrar(lat)
        self._limpar_saida()
        return ResultadoTurno(pergunta, resposta, fala, saida, lat, motivo)

    def _limpar_saida(self) -> None:
        """Retenção mínima: mantém só as últimas respostas sintetizadas."""
        arquivos = sorted(SAIDA_DIR.glob("resp_*"), key=lambda p: p.stat().st_mtime)
        for antigo in arquivos[:-MANTER_AUDIOS]:
            antigo.unlink(missing_ok=True)

    def _registrar(self, lat: dict[str, float]) -> None:
        if not self.log_latencia:
            return
        novo = not self.log_latencia.exists()
        with open(self.log_latencia, "a", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(lat))
            if novo:
                w.writeheader()
            w.writerow({k: round(v, 3) for k, v in lat.items()})
