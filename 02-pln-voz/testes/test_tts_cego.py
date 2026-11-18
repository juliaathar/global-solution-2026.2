"""Testes da avaliação cega do TTS (sem áudio real: o PyAV é trocado por uma cópia simples)."""
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
import tts_cego  # noqa: E402
from util import escrever_csv, ler_csv  # noqa: E402


class Base(unittest.TestCase):
    def setUp(self):
        self.t = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.t)
        linhas = [{"motor": m, "id": f"r{i:02d}", "arquivo": f"{m}_r{i:02d}.x", "avaliador": a,
                   "naturalidade": "", "clareza": ""}
                  for m in ("piper", "edge-tts") for i in (1, 2, 3) for a in tts_cego.AVALIADORES]
        self.planilha = self.t / "planilha.csv"
        escrever_csv(self.planilha, linhas)
        self.kw = dict(planilha=self.planilha, pasta_audios=self.t / "tts", pasta=self.t / "cego",
                       notas=self.t / "notas.csv", chave=self.t / "chave.csv")

    def preparar(self, **extra):
        copiar = lambda o, d: (d.parent.mkdir(parents=True, exist_ok=True), d.write_bytes(b"x"))  # noqa: E731
        with mock.patch.object(tts_cego, "_converter", side_effect=copiar):
            return tts_cego.preparar(**self.kw, **extra)


class TestPreparar(Base):
    def test_cria_nomes_neutros_e_chave(self):
        chave = self.preparar()
        self.assertEqual(len(chave), 6)
        self.assertEqual(sorted(p.name for p in (self.t / "cego").iterdir()), [f"aval_0{i}.wav" for i in range(1, 7)])
        self.assertTrue(all("piper" not in k["aval"] and "edge" not in k["aval"] for k in chave))
        self.assertEqual(len(ler_csv(self.t / "notas.csv")), 18)  # 6 áudios x 3 avaliadores

    def test_ordem_embaralhada_mas_reproduzivel(self):
        a = [k["arquivo"] for k in self.preparar()]
        self.assertNotEqual(a, sorted(a))
        (self.t / "notas.csv").unlink(); (self.t / "chave.csv").unlink()
        self.assertEqual(a, [k["arquivo"] for k in self.preparar()])

    def test_nao_apaga_notas_existentes_sem_forcar(self):
        self.preparar()
        with self.assertRaises(SystemExit):
            self.preparar()
        self.preparar(forcar=True)


class TestConsolidar(Base):
    def _preencher(self, nomes=("Ana", "Bia", "Caio"), nota="4"):
        self.preparar()
        linhas = ler_csv(self.t / "notas.csv")
        mapa = dict(zip(tts_cego.AVALIADORES, nomes))
        for l in linhas:
            l["avaliador"], l["naturalidade"], l["clareza"] = mapa[l["avaliador"]], nota, nota
        escrever_csv(self.t / "notas.csv", linhas)

    def test_consolida_na_planilha_oficial(self):
        self._preencher()
        linhas, problemas = tts_cego.consolidar(self.t / "notas.csv", self.t / "chave.csv", self.planilha)
        self.assertEqual(problemas, [])
        p = ler_csv(self.planilha)
        self.assertEqual(len(p), 18)
        self.assertEqual({l["avaliador"] for l in p}, {"Ana", "Bia", "Caio"})
        self.assertEqual({l["motor"] for l in p}, {"piper", "edge-tts"})  # a chave devolve o motor certo

    def test_nota_invalida_ou_vazia_nao_consolida(self):
        self._preencher(nota="7")
        _, problemas = tts_cego.consolidar(self.t / "notas.csv", self.t / "chave.csv", self.planilha)
        self.assertTrue(any("1 a 5" in p for p in problemas))
        self.assertEqual(len(ler_csv(self.planilha)), 18)  # planilha original intocada (ainda com notas vazias)
        self.assertEqual({l["naturalidade"] for l in ler_csv(self.planilha)}, {""})

    def test_exige_tres_pessoas_e_nomes_reais(self):
        self._preencher(nomes=("Ana", "Ana", "Bia"))
        _, problemas = tts_cego.consolidar(self.t / "notas.csv", self.t / "chave.csv", self.planilha)
        self.assertTrue(any("3 pessoas" in p for p in problemas))
        # nomes genéricos
        linhas = ler_csv(self.t / "notas.csv")
        for i, l in enumerate(linhas):
            l["avaliador"] = tts_cego.AVALIADORES[i % 3]
        escrever_csv(self.t / "notas.csv", linhas)
        _, problemas = tts_cego.consolidar(self.t / "notas.csv", self.t / "chave.csv", self.planilha)
        self.assertTrue(any("nomes reais" in p for p in problemas))


if __name__ == "__main__":
    unittest.main()
