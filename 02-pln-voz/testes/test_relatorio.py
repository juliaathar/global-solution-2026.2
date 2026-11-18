import importlib.util
import tempfile
import unittest
from pathlib import Path

from util import RAIZ

_spec = importlib.util.spec_from_file_location("montar", RAIZ / "relatorio" / "montar.py")
montar = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(montar)


class TesteMontagem(unittest.TestCase):
    def test_inclui_evidencia_e_rebaixa_titulos(self):
        with tempfile.TemporaryDirectory() as d:
            raiz = Path(d)
            (raiz / "evidencias").mkdir()
            (raiz / "evidencias" / "a.md").write_text("# Titulo\n\n## Sub\ntexto", encoding="utf-8")
            texto, faltando, pend = montar.montar("### 6.1\n<!-- INCLUIR: evidencias/a.md -->", raiz)
            self.assertIn("#### Titulo", texto)
            self.assertIn("##### Sub", texto)
            self.assertEqual((faltando, pend), ([], 0))

    def test_evidencia_ausente_vira_aviso(self):
        with tempfile.TemporaryDirectory() as d:
            texto, faltando, _ = montar.montar("<!-- INCLUIR: evidencias/x.md -->", Path(d))
            self.assertEqual(faltando, ["evidencias/x.md"])
            self.assertIn("FALTA", texto)

    def test_conta_pendencias(self):
        _, _, pend = montar.montar("[PREENCHER: a] e [PREENCHER: b]", Path("."))
        self.assertEqual(pend, 2)

    def test_remove_instrucoes(self):
        t = "# A\n\n> **Escrever:** faça isso\n> segunda linha\n\ntexto\n\n> citação normal\n"
        saida = montar.remover_instrucoes(t)
        self.assertNotIn("faça isso", saida)
        self.assertNotIn("segunda linha", saida)
        self.assertIn("texto", saida)
        self.assertIn("citação normal", saida)

    def test_esqueleto_real_tem_marcadores_validos(self):
        texto = (RAIZ / "relatorio" / "relatorio.md").read_text(encoding="utf-8")
        alvos = montar.MARCADOR.findall(texto)
        self.assertEqual(sorted(alvos), sorted(["evidencias/stt_resumo.md", "evidencias/sintetico/stt_resumo.md",
                                                "evidencias/llm_resumo.md", "evidencias/tts_resumo.md",
                                                "evidencias/sintetico/e2e_resumo.md",
                                                "evidencias/e2e_resumo.md"]))
        for t in ("Problema", "ODS", "Arquitetura", "Justificativa", "LGPD", "Limitações", "Conclusão"):
            self.assertIn(t, texto)


if __name__ == "__main__":
    unittest.main()
