"""Testes do robô RPA. Rodar de 06-rpa/: python -m unittest discover -s testes -v"""
import csv
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "codigo"))

import config  # noqa: E402
from classificador import classificar  # noqa: E402
from deduplicacao import eh_duplicado, normalizar  # noqa: E402
from ingestao import ler_relatos  # noqa: E402
from notificador import ErroNotificacao, enviar_com_retry  # noqa: E402
from validacao import validar  # noqa: E402


class TestRPA(unittest.TestCase):
    def test_validacao_rejeita_vazio_curto_longo(self):
        self.assertFalse(validar({"id": "1", "texto": ""})[0])
        self.assertFalse(validar({"id": "1", "texto": "oi"})[0])
        self.assertFalse(validar({"id": "1", "texto": "x" * 900})[0])
        self.assertTrue(validar({"id": "1", "texto": "Buraco na rua principal"})[0])

    def test_arquivo_ausente_nao_derruba(self):
        self.assertEqual(ler_relatos(Path("nao_existe.csv")), [])

    def test_duplicado_ignora_acento_e_caixa(self):
        vistos = [normalizar("Buraco na Rua das Flores")]
        self.assertTrue(eh_duplicado("buraco na rua das flôres", vistos, 0.85))
        self.assertFalse(eh_duplicado("Poste apagado na Av. Brasil", vistos, 0.85))

    def test_classificador_urgencia_e_indefinido(self):
        self.assertEqual(classificar("Buraco perigoso, houve acidente")["urgencia"], "alta")
        self.assertEqual(classificar("Preciso de ajuda com uma coisa")["categoria"], "indefinido")

    def test_retry_recupera_falha_transitoria(self):
        chamadas = {"n": 0}

        def instavel(_):
            chamadas["n"] += 1
            if chamadas["n"] < 3:
                raise ErroNotificacao("fora do ar")

        self.assertTrue(enviar_com_retry("P1", 3, 0, enviar_fn=instavel))
        self.assertEqual(chamadas["n"], 3)

    def test_retry_desiste_sem_quebrar(self):
        def sempre_falha(_):
            raise ErroNotificacao("fora do ar")

        self.assertFalse(enviar_com_retry("P1", 2, 0, enviar_fn=sempre_falha))

    def test_idempotencia_duas_execucoes(self):
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            entrada = d / "r.csv"
            with open(entrada, "w", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=["id", "texto"])
                w.writeheader()
                w.writerow({"id": "A1", "texto": "Buraco grande na Rua Sete"})
                w.writerow({"id": "A2", "texto": "Poste apagado na Av. Central"})
            config.SAIDA = d / "saida"
            config.BANCO = config.SAIDA / "p.db"
            config.RELATORIO = config.SAIDA / "r.json"
            config.REVISAO = config.SAIDA / "rev.csv"
            import main
            primeira = main.executar(entrada)["resumo"]
            segunda = main.executar(entrada)["resumo"]
            self.assertEqual(primeira["protocolos"], 2)
            self.assertEqual(segunda["protocolos"], 0)
            self.assertEqual(segunda["ja_processados"], 2)


if __name__ == "__main__":
    unittest.main()
