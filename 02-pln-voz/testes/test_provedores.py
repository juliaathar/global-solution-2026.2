"""Testes dos provedores de LLM (sem rede)."""
import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from llm.provedores import OllamaLLM, OpenAICompatLLM, criar_llm  # noqa: E402


class TestProvedores(unittest.TestCase):
    def test_provedores_do_env_example_da_raiz_sao_aceitos(self):
        # O .env.example da raiz lista openai, groq, gemini e ollama como valores de LLM_PROVIDER.
        for p in ("openai", "groq", "gemini"):
            self.assertIsInstance(criar_llm(p, "modelo", "chave"), OpenAICompatLLM)
        self.assertIsInstance(criar_llm("ollama", "qwen2.5:3b"), OllamaLLM)

    def test_provedor_desconhecido_da_erro_claro(self):
        with self.assertRaises(ValueError) as e:
            criar_llm("xyz", "m")
        self.assertIn("xyz", str(e.exception))

    def test_ollama_usa_a_url_do_ambiente(self):
        with mock.patch.dict("os.environ", {"OLLAMA_URL": "http://servidor:1234"}):
            self.assertEqual(criar_llm("ollama", "m").url, "http://servidor:1234")


if __name__ == "__main__":
    unittest.main()


class TestTempoLimite(unittest.TestCase):
    def _chamar(self, llm):
        resposta = mock.Mock()
        resposta.json.return_value = {"message": {"content": "ok"}, "choices": [{"message": {"content": "ok"}}]}
        with mock.patch("llm.provedores.requests.post", return_value=resposta) as post:
            llm.responder("sistema", [], [])
        return post.call_args.kwargs["timeout"]

    def test_padroes_sao_mantidos(self):
        with mock.patch.dict("os.environ", {}, clear=False):
            import os
            os.environ.pop("LLM_TIMEOUT_S", None)
            self.assertEqual(self._chamar(criar_llm("ollama", "m")), 120)
            self.assertEqual(self._chamar(criar_llm("groq", "m", "k")), 60)

    def test_llm_timeout_s_vale_para_todos(self):
        with mock.patch.dict("os.environ", {"LLM_TIMEOUT_S": "900"}):
            self.assertEqual(self._chamar(criar_llm("ollama", "m")), 900)
            self.assertEqual(self._chamar(criar_llm("openai", "m", "k")), 900)

    def test_valor_invalido_cai_no_padrao(self):
        with mock.patch.dict("os.environ", {"LLM_TIMEOUT_S": "abc"}):
            self.assertEqual(self._chamar(criar_llm("ollama", "m")), 120)
