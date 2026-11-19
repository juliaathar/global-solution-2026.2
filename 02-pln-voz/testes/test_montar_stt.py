"""Testes do montador do conjunto de STT (com áudios sintéticos)."""
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import montar_stt_das_conversas as ms  # noqa: E402
import organizar_audios as oa  # noqa: E402
from test_organizar_audios import tom  # noqa: E402
from util import escrever_csv, ler_csv  # noqa: E402


class TestMontar(unittest.TestCase):
    def setUp(self):
        self.t = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.t)
        self.ent = self.t / "entrada"
        self.ent.mkdir()
        escrever_csv(self.ent / "vozes.csv", [{"falante": f, "quem": f, "faixa_etaria": "20 a 30",
                                                "sotaque": "paulista", "consentimento": "sim"} for f in "ABC"])
        self.i = 0

    def _gravar(self, cod):
        self.i += 1
        tom(self.ent / f"{cod}.wav", seg=1.0 + 0.1 * self.i)  # duração diferente: não é áudio repetido

    def _tudo(self):
        for _, cod in ms.LIMPOS.values():
            self._gravar(cod)
        for r in ms.RUIDOSOS:
            self._gravar(r)

    def montar(self):
        return ms.montar(self.ent, self.t / "stt", self.t / "manifesto.csv")

    def test_regra_tem_15_limpos_5_por_voz_e_5_ruidosos(self):
        voz = [v for v, _ in ms.LIMPOS.values()]
        self.assertEqual((len(ms.LIMPOS), len(ms.RUIDOSOS)), (15, 5))
        self.assertEqual({v: voz.count(v) for v in "ABC"}, {"A": 5, "B": 5, "C": 5})
        self.assertFalse(set(ms.LIMPOS) & set(ms.RUIDOSOS))  # nenhuma vaga repetida
        self.assertEqual(len(set(c for _, c in ms.LIMPOS.values())), 15)  # nenhuma conversa repetida

    def test_monta_20_audios_e_manifesto_com_3_vozes_e_5_ruidos(self):
        self._tudo()
        linhas, problemas = self.montar()
        self.assertEqual(problemas, [])
        self.assertEqual(len(list((self.t / "stt").glob("*.wav"))), 20)
        m = ler_csv(self.t / "manifesto.csv")
        self.assertEqual({l["falante"] for l in m}, {"A", "B", "C"})
        self.assertEqual(sum(l["ruido"] == "sim" for l in m), 5)
        self.assertTrue(all(l["faixa_etaria"] == "20 a 30" for l in m))

    def test_referencia_dos_limpos_e_a_frase_da_conversa(self):
        self._tudo()
        linhas, _ = self.montar()
        ref = {l["arquivo"]: l["referencia"] for l in linhas}
        self.assertEqual(ref["stt_01.wav"], "Quais documentos preciso para fazer o Cadastro Único?")  # c01_t1
        self.assertEqual(ref["stt_03.wav"], "O que eu preciso levar para ser atendido na UBS?")        # ruidoso: frase original

    def test_ruidosos_sao_todos_da_voz_a(self):
        self._tudo()
        linhas, _ = self.montar()
        self.assertEqual({l["falante"] for l in linhas if l["ruido"] == "sim"}, {"A"})

    def test_falta_audio_nao_grava_nada(self):
        self._tudo()
        (self.ent / "c04_t1.wav").unlink()
        linhas, problemas = self.montar()
        self.assertTrue(any("c04_t1" in p for p in problemas))
        self.assertFalse((self.t / "stt").exists())
        self.assertFalse((self.t / "manifesto.csv").exists())


if __name__ == "__main__":
    unittest.main()
