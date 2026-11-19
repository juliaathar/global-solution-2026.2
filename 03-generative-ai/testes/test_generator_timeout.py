"""O limite de espera do LLM vem de LLM_TIMEOUT_S (padrão 60 s): em CPU sem GPU o modelo local passa de 1 minuto."""
import os
import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from rag.generator import generator  # noqa: E402


class TestTimeout(unittest.TestCase):
    def test_padrao_continua_60(self):
        with mock.patch.dict(os.environ):
            os.environ.pop("LLM_TIMEOUT_S", None)
            self.assertEqual(generator._timeout_s(), 60.0)

    def test_variavel_de_ambiente_vale(self):
        with mock.patch.dict(os.environ, {"LLM_TIMEOUT_S": "300"}):
            self.assertEqual(generator._timeout_s(), 300.0)

    def test_valor_invalido_cai_no_padrao(self):
        with mock.patch.dict(os.environ, {"LLM_TIMEOUT_S": "abc"}):
            self.assertEqual(generator._timeout_s(), 60.0)

    def test_a_chamada_ao_llm_usa_o_limite_da_constante(self):
        self.assertEqual(generator.TIMEOUT_S, generator._timeout_s())


if __name__ == "__main__":
    unittest.main()
