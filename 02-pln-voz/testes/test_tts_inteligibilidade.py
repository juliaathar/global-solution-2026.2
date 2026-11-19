"""Testes da clareza objetiva do TTS (com um STT falso)."""
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import avaliar_tts_inteligibilidade as ti  # noqa: E402


class STTFalso:
    def __init__(self, respostas):
        self.respostas = respostas

    def transcrever(self, caminho):
        r = self.respostas[Path(caminho).stem]
        if isinstance(r, Exception):
            raise r
        return r


class TestInteligibilidade(unittest.TestCase):
    def setUp(self):
        self.d = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.d)
        for n in ("piper_r01.wav", "edge-tts_r01.mp3", "piper_r02.wav"):
            (self.d / n).write_bytes(b"x")
        self.linhas = [{"motor": "piper", "id": "r01", "texto_falado": "A UBS abre às sete horas."},
                       {"motor": "edge-tts", "id": "r01", "texto_falado": "A UBS abre às sete horas."},
                       {"motor": "piper", "id": "r02", "texto_falado": "Leve o documento."},
                       {"motor": "piper", "id": "r03", "texto_falado": "Sem áudio."}]

    def test_wer_zero_quando_reconhece_tudo_e_acha_o_arquivo_pela_extensao_do_motor(self):
        stt = STTFalso({"piper_r01": "A UBS abre às sete horas.", "edge-tts_r01": "a ubs abre às 7 horas",
                        "piper_r02": "Leve o documento."})
        res = ti.avaliar(stt, self.linhas, self.d)
        por = {(r["motor"], r["id"]): r for r in res}
        self.assertEqual(por[("piper", "r01")]["wer"], 0.0)
        self.assertEqual(por[("edge-tts", "r01")]["wer"], 0.0)  # "7" e "sete" são equivalentes na normalização
        self.assertEqual(por[("edge-tts", "r01")]["arquivo"], "edge-tts_r01.mp3")

    def test_erro_de_reconhecimento_aparece_no_wer(self):
        stt = STTFalso({"piper_r01": "A UBS abre às nove horas.", "edge-tts_r01": "x", "piper_r02": "Leve o documento."})
        res = ti.avaliar(stt, self.linhas, self.d)
        self.assertGreater([r for r in res if r["motor"] == "piper" and r["id"] == "r01"][0]["wer"], 0)

    def test_audio_ausente_e_falha_do_stt_nao_derrubam(self):
        stt = STTFalso({"piper_r01": TimeoutError("x"), "edge-tts_r01": "a", "piper_r02": "b"})
        res = ti.avaliar(stt, self.linhas, self.d)
        por = {(r["motor"], r["id"]): r for r in res}
        self.assertEqual(por[("piper", "r03")]["erro"], "áudio não encontrado")
        self.assertEqual(por[("piper", "r01")]["erro"], "TimeoutError")
        self.assertEqual(len(res), 4)

    def test_resumo_diz_que_nao_mede_naturalidade(self):
        stt = STTFalso({"piper_r01": "A UBS abre às sete horas.", "edge-tts_r01": "a", "piper_r02": "Leve o documento."})
        md = ti.resumir(ti.avaliar(stt, self.linhas, self.d), "small")
        self.assertIn("não** mede naturalidade", md)
        self.assertIn("piper", md)


if __name__ == "__main__":
    unittest.main()
