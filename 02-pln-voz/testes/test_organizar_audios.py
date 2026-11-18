"""Testes do organizador de áudios, com áudios sintéticos gerados na hora (sem gravações reais)."""
import shutil
import sys
import tempfile
import unittest
import wave
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import organizar_audios as oa  # noqa: E402
from util import escrever_csv, ler_csv  # noqa: E402


def tom(caminho: Path, seg=3.0, taxa=44100, canais=2, amp=0.3, ruido=0.0):
    t = np.arange(int(seg * taxa)) / taxa
    x = amp * np.sin(2 * np.pi * 220 * t) * (np.sin(2 * np.pi * 3 * t) > -0.3)  # "fala" com pausas
    x = x + ruido * np.random.default_rng(1).standard_normal(len(x))
    pcm = (np.clip(x, -1, 1) * 32767).astype("<i2")
    if canais == 2:
        pcm = np.repeat(pcm[:, None], 2, axis=1).reshape(-1)
    with wave.open(str(caminho), "wb") as w:
        w.setnchannels(canais); w.setsampwidth(2); w.setframerate(taxa); w.writeframes(pcm.tobytes())


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.entrada, self.saida, self.evid = self.tmp / "entrada", self.tmp / "saida", self.tmp / "evid"
        self.entrada.mkdir()
        self.saida.mkdir()
        shutil.copy(oa.AUDIOS / "manifesto_stt.csv", self.saida / "manifesto_stt.csv")
        self.addCleanup(shutil.rmtree, self.tmp)

    def vozes(self, consentimento="sim"):
        escrever_csv(self.entrada / "vozes.csv", [
            {"falante": f, "quem": f"pessoa {f}", "faixa_etaria": "20 a 30", "sotaque": "paulista",
             "consentimento": consentimento} for f in "ABC"])

    def rodar(self, **kw):
        return oa.organizar(self.entrada, saida=self.saida, evidencias=self.evid, **kw)


class TestConversao(Base):
    def test_wav_estereo_44k_vira_mono_16k(self):
        tom(self.entrada / "x.wav", seg=2.0)
        x = oa.carregar(self.entrada / "x.wav")
        self.assertAlmostEqual(len(x) / oa.TAXA, 2.0, places=2)

    def test_gravar_e_reler(self):
        x = np.zeros(oa.TAXA, dtype=np.float32)
        oa.gravar_wav(self.tmp / "y.wav", x)
        with wave.open(str(self.tmp / "y.wav")) as w:
            self.assertEqual((w.getnchannels(), w.getframerate(), w.getsampwidth()), (1, 16000, 2))


class TestFormatosDeCelular(Base):
    """m4a (iPhone/Android), opus (WhatsApp) e mp3 passam pelo PyAV. Pula se o av ou o codificador faltar."""

    def _codificar(self, nome, codec):
        try:
            import av
        except ImportError:
            self.skipTest("pacote av não instalado")
        x = (0.3 * np.sin(2 * np.pi * 220 * np.arange(96000) / 48000)).astype(np.float32)
        try:
            c = av.open(str(self.tmp / nome), "w")
            st = c.add_stream(codec, rate=48000)
            st.layout = "mono"
            fr = av.AudioFrame.from_ndarray(x.reshape(1, -1), format="flt", layout="mono")
            fr.sample_rate = 48000
            for p in st.encode(fr):
                c.mux(p)
            for p in st.encode(None):
                c.mux(p)
            c.close()
        except Exception as e:  # noqa: BLE001 - codificador ausente nesta instalação
            self.skipTest(f"sem codificador {codec}: {e}")
        return self.tmp / nome

    def test_formatos(self):
        for nome, codec in (("a.m4a", "aac"), ("b.opus", "libopus"), ("c.mp3", "libmp3lame")):
            with self.subTest(nome):
                caminho = self._codificar(nome, codec)
                x = oa.carregar(caminho)
                self.assertAlmostEqual(len(x) / oa.TAXA, 2.0, delta=0.1)
                self.assertGreater(oa.medir(x)["nivel_dbfs"], -25)


class TestOrganizar(Base):
    def test_nome_do_arquivo_e_o_codigo(self):
        self.vozes()
        tom(self.entrada / "stt_01.wav"); tom(self.entrada / "c01_t1.wav")
        r = self.rodar()
        self.assertEqual(r["problemas"], [])
        self.assertTrue((self.saida / "stt" / "stt_01.wav").is_file())
        self.assertTrue((self.saida / "e2e" / "c01_t1.wav").is_file())
        self.assertEqual(len(r["faltando"]), 48)  # 50 esperados - 2
        with wave.open(str(self.saida / "stt" / "stt_01.wav")) as w:
            self.assertEqual((w.getnchannels(), w.getframerate()), (1, 16000))

    def test_mapeamento_csv_renomeia(self):
        self.vozes()
        tom(self.entrada / "AUD-0001.wav")
        escrever_csv(self.entrada / "mapeamento.csv", [{"original": "AUD-0001.wav", "codigo": "stt_08.wav"}])
        r = self.rodar()
        self.assertEqual(r["problemas"], [])
        self.assertTrue((self.saida / "stt" / "stt_08.wav").is_file())

    def test_arquivo_sem_codigo_e_apontado(self):
        self.vozes()
        tom(self.entrada / "audio_qualquer.wav")
        r = self.rodar()
        self.assertTrue(any("audio_qualquer.wav" in p for p in r["problemas"]))

    def test_sem_consentimento_nao_processa(self):
        self.vozes(consentimento="nao")
        tom(self.entrada / "stt_01.wav")
        r = self.rodar()
        self.assertTrue(any("consentimento" in p for p in r["problemas"]))
        self.assertFalse((self.saida / "stt" / "stt_01.wav").exists())

    def test_sem_vozes_csv_avisa(self):
        tom(self.entrada / "stt_01.wav")
        r = self.rodar()
        self.assertTrue(any("vozes.csv" in p for p in r["problemas"]))

    def test_so_conferir_nao_grava(self):
        self.vozes()
        tom(self.entrada / "stt_01.wav")
        r = self.rodar(so_conferir=True)
        self.assertEqual(len(r["linhas"]), 1)
        self.assertFalse((self.saida / "stt").exists())

    def test_nao_sobrescreve_sem_forcar(self):
        self.vozes()
        tom(self.entrada / "stt_01.wav")
        self.assertEqual(self.rodar()["problemas"], [])
        self.assertTrue(any("já existe" in p for p in self.rodar()["problemas"]))
        self.assertEqual(self.rodar(forcar=True)["problemas"], [])

    def test_preenche_faixa_etaria_e_sotaque_no_manifesto(self):
        self.vozes()
        tom(self.entrada / "stt_01.wav")
        self.rodar()
        m = {l["arquivo"]: l for l in ler_csv(self.saida / "manifesto_stt.csv")}
        self.assertEqual((m["stt_01.wav"]["faixa_etaria"], m["stt_01.wav"]["sotaque"]), ("20 a 30", "paulista"))
        self.assertEqual(m["stt_20.wav"]["sotaque"], "paulista")  # a voz C também (todas as linhas da voz)

    def test_arquivo_corrompido_nao_derruba(self):
        self.vozes()
        (self.entrada / "stt_01.wav").write_bytes(b"isto nao e um audio")
        tom(self.entrada / "stt_02.wav")
        r = self.rodar()
        self.assertTrue(any("stt_01.wav" in p and "não foi possível ler" in p for p in r["problemas"]))
        self.assertTrue((self.saida / "stt" / "stt_02.wav").is_file())


class TestQualidade(Base):
    def test_avisos(self):
        self.assertIn("muito curto", oa.avisos_de(oa.medir(np.zeros(1000, dtype=np.float32) + 0.2)))
        self.assertIn("quase mudo", oa.avisos_de(oa.medir(np.zeros(oa.TAXA * 3, dtype=np.float32))))
        estourado = np.ones(oa.TAXA * 3, dtype=np.float32)
        self.assertIn("áudio estourado (clipping)", oa.avisos_de(oa.medir(estourado)))
        t = np.arange(oa.TAXA * 3) / oa.TAXA
        ok = (0.3 * np.sin(2 * np.pi * 220 * t)).astype(np.float32)
        self.assertEqual(oa.avisos_de(oa.medir(ok)), [])

    def test_ruido_marcado_mas_silencioso_gera_aviso(self):
        base = [{"ruido": "nao", "piso_ruido_dbfs": -60.0, "avisos": ""} for _ in range(5)]
        sim = {"ruido": "sim", "piso_ruido_dbfs": -59.0, "avisos": ""}
        oa.conferir_ruido(base + [sim])
        self.assertIn("ruído pouco perceptível", sim["avisos"])
        ok = {"ruido": "sim", "piso_ruido_dbfs": -35.0, "avisos": ""}
        oa.conferir_ruido(base + [ok])
        self.assertEqual(ok["avisos"], "")

    def test_piso_de_ruido_sobe_com_ruido_de_fundo(self):
        limpo, sujo = self.tmp / "l.wav", self.tmp / "s.wav"
        tom(limpo, canais=1, ruido=0.0005)
        tom(sujo, canais=1, ruido=0.05)
        self.assertGreater(oa.medir(oa.carregar(sujo))["piso_ruido_dbfs"],
                           oa.medir(oa.carregar(limpo))["piso_ruido_dbfs"] + 15)


class TestCodigosEsperados(unittest.TestCase):
    def test_50_codigos(self):
        e = oa.codigos_esperados()
        self.assertEqual(sum(1 for v in e.values() if v["pasta"] == "stt"), 20)
        self.assertEqual(sum(1 for v in e.values() if v["pasta"] == "e2e"), 30)
        self.assertEqual(sum(1 for v in e.values() if v["ruido"] == "sim"), 5)


if __name__ == "__main__":
    unittest.main()
