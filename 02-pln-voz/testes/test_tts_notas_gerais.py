"""Testes da avaliação do TTS por nota geral (importação, conversão de escala e resumo)."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import tts_notas_gerais as tn  # noqa: E402


class TestConversao(unittest.TestCase):
    def test_extremos_preservados(self):
        self.assertEqual(tn.converter(1), 1.0)
        self.assertEqual(tn.converter(10), 5.0)

    def test_valores_intermediarios(self):
        self.assertAlmostEqual(tn.converter(7), 1 + 6 * 4 / 9)
        self.assertAlmostEqual(tn.converter(8), 1 + 7 * 4 / 9)
        self.assertTrue(all(1 <= tn.converter(n) <= 5 for n in range(1, 11)))

    def test_monotonica(self):
        v = [tn.converter(n) for n in range(1, 11)]
        self.assertEqual(v, sorted(v))


class TestImportar(unittest.TestCase):
    def test_tres_notas_seguidas_por_audio_na_ordem(self):
        seq = " ".join(str(i % 10 + 1) for i in range(60))
        linhas = tn.importar(seq)
        self.assertEqual(len(linhas), 60)
        self.assertEqual([(l["aval"], l["dupla"]) for l in linhas[:4]],
                         [("aval_01", 1), ("aval_01", 2), ("aval_01", 3), ("aval_02", 1)])
        self.assertEqual(linhas[-1]["aval"], "aval_20")

    def test_quantidade_errada_e_nota_fora_da_escala_sao_recusadas(self):
        with self.assertRaises(ValueError):
            tn.importar("7 8 9")
        with self.assertRaises(ValueError):
            tn.importar(" ".join(["11"] * 60))
        with self.assertRaises(ValueError):
            tn.importar(" ".join(["0"] * 60))
        with self.assertRaises(ValueError):
            tn.importar("a " * 60)


class TestResumo(unittest.TestCase):
    def setUp(self):
        self.chave = ([{"aval": f"aval_{i:02d}", "motor": "edge-tts", "id": f"r{i:02d}", "arquivo": f"edge-tts_r{i:02d}.mp3"}
                       for i in range(1, 11)]
                      + [{"aval": f"aval_{i + 10:02d}", "motor": "piper", "id": f"r{i:02d}", "arquivo": f"piper_r{i:02d}.wav"}
                         for i in range(1, 11)])

    def _linhas(self, nota_edge, nota_piper):
        notas = []
        for k in self.chave:
            v = nota_edge if k["motor"] == "edge-tts" else nota_piper
            notas += [{"aval": k["aval"], "dupla": d, "nota_1a10": v} for d in (1, 2, 3)]
        return tn.consolidar(notas, self.chave)

    def test_consolidar_junta_com_a_chave_e_converte(self):
        linhas = self._linhas(10, 1)
        self.assertEqual(len(linhas), 60)
        edge = [l for l in linhas if l["motor"] == "edge-tts"]
        self.assertTrue(all(l["nota_1a5"] == 5.0 for l in edge))
        self.assertTrue(all(l["nota_1a5"] == 1.0 for l in linhas if l["motor"] == "piper"))

    def test_resumo_traz_medias_por_motor_e_comparacao_pareada(self):
        md = tn.resumir(self._linhas(10, 1))
        self.assertIn("edge-tts", md)
        self.assertIn("5.00", md.replace(",", "."))
        self.assertIn("Em 10 frases: `edge-tts` teve nota maior em 10", md)
        self.assertIn("Naturalidade e clareza não foram avaliadas separadamente", md)

    def test_empate_e_contado(self):
        md = tn.resumir(self._linhas(8, 8))
        self.assertIn("empate em 10", md)


if __name__ == "__main__":
    unittest.main()
