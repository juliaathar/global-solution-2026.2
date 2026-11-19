"""Testes dos scripts de avaliação (STT, LLM, TTS, ponta a ponta) e dos dados de teste."""
import importlib.util
import shutil
import tempfile
import unittest
from pathlib import Path

from util import AUDIOS, RAIZ, TESTES, ler_csv  # noqa: F401  (util ajusta o sys.path)

import avaliar_e2e
import avaliar_llm
import avaliar_stt
import avaliar_tts
from componentes import DemoLLM, DemoSTT, DemoTTS, tom_wav
from interfaces import Trecho
from llm.base_stub import BaseStub

TEM_JIWER = importlib.util.find_spec("jiwer") is not None


class TesteDadosEntregues(unittest.TestCase):
    """Os arquivos de teste do grupo cumprem os mínimos do enunciado."""

    def test_perguntas_llm(self):
        p = ler_csv(TESTES / "perguntas_llm.csv")
        tipos = [l["tipo"] for l in p]
        self.assertEqual(len(p), 30)
        self.assertEqual(tipos.count("continuacao"), 5)
        self.assertEqual(tipos.count("fora_escopo"), 5)
        for l in p:
            if l["tipo"] == "continuacao":  # precisa ter turno anterior na mesma conversa
                self.assertGreater(int(l["turno"]), 1)
            if l["tipo"] in ("normal", "continuacao"):
                self.assertTrue(l["esperado"], l["id"])

    def test_manifesto_stt(self):
        m = ler_csv(AUDIOS / "manifesto_stt.csv")
        self.assertEqual(len(m), 20)
        self.assertGreaterEqual(len({l["falante"] for l in m}), 3)
        self.assertEqual(sum(l["ruido"] == "sim" for l in m), 5)
        self.assertEqual(len({l["arquivo"] for l in m}), 20)

    def test_conversas_e2e(self):
        c = ler_csv(TESTES / "conversas_e2e.csv")
        por = {}
        for l in c:
            por.setdefault(l["conversa"], []).append(l)
        self.assertEqual(len(por), 10)
        self.assertTrue(all(len(v) >= 3 for v in por.values()))

    def test_respostas_tts(self):
        self.assertEqual(len(ler_csv(TESTES / "respostas_tts.csv")), 10)


@unittest.skipUnless(TEM_JIWER, "jiwer não instalado")
class TesteSTT(unittest.TestCase):
    def test_normalizacao(self):
        self.assertEqual(avaliar_stt.normalizar("A UBS abre às 7h?"), "a ubs abre às sete horas")
        self.assertEqual(avaliar_stt.normalizar("u b s"), "ubs")
        self.assertEqual(avaliar_stt.normalizar("Olá, mundo!"), "olá mundo")
        self.assertEqual(avaliar_stt.normalizar("Custa R$ 50 e 10%"), "custa cinquenta reais e dez por cento")

    def test_wer(self):
        self.assertEqual(avaliar_stt.wer("a ubs abre hoje", "A UBS abre hoje."), 0)
        self.assertAlmostEqual(avaliar_stt.wer("a ubs abre hoje", "a ubs fecha hoje"), 0.25)
        self.assertEqual(avaliar_stt.wer("a ubs abre", ""), 1.0)

    def test_avaliar_e_resumir(self):
        class Fake:
            def __init__(self, resp): self.resp = resp
            def transcrever(self, p): return self.resp

        linhas = [{"arquivo": "a.wav", "falante": "A", "ruido": "nao", "referencia": "a ubs abre hoje"},
                  {"arquivo": "b.wav", "falante": "B", "ruido": "sim", "referencia": "o cras atende hoje"}]
        res = avaliar_stt.avaliar({"bom": Fake("a ubs abre hoje"), "ruim": Fake("nada")}, linhas, Path("."))
        self.assertEqual(len(res), 4)
        md = avaliar_stt.resumir(res)
        for trecho in ("bom", "ruim", "Viés: Falante", "Viés: Ruído de fundo", "WER global"):
            self.assertIn(trecho, md)

    def test_arquivos_faltando(self):
        self.assertEqual(avaliar_stt.arquivos_faltando([{"arquivo": "nao_existe.wav"}], Path(".")),
                         ["nao_existe.wav"])


class TesteLLM(unittest.TestCase):
    def test_satisfaz(self):
        self.assertTrue(avaliar_llm.satisfaz("Abre às SETE horas", "sete|7"))
        self.assertTrue(avaliar_llm.satisfaz("segunda a sexta", "segunda;sexta"))
        self.assertFalse(avaliar_llm.satisfaz("só segunda", "segunda;sexta"))
        self.assertTrue(avaliar_llm.satisfaz("Certidão e comprovante", "certidao;comprovante"))

    def test_recusa(self):
        self.assertTrue(avaliar_llm.eh_recusa("Não sei essa informação.", "llm"))
        self.assertTrue(avaliar_llm.eh_recusa("qualquer", "sem_contexto"))
        self.assertFalse(avaliar_llm.eh_recusa("A UBS abre às sete.", "llm"))

    def test_julgar(self):
        self.assertTrue(avaliar_llm.julgar("normal", "sete", "abre às sete", "llm"))
        self.assertFalse(avaliar_llm.julgar("normal", "sete", "Não sei, talvez sete", "llm"))
        self.assertTrue(avaliar_llm.julgar("fora_escopo", "", "Não posso ajudar com isso", "llm"))
        self.assertFalse(avaliar_llm.julgar("fora_escopo", "", "O Flamengo ganhou de 2 a 0", "llm"))

    def test_executar_com_memoria_e_resumo(self):
        class LLM:
            nome = "falso"
            def responder(self, system, historico, contexto):
                return "A UBS abre às sete e pede documento com foto e cartão do SUS."

        # Fixture própria (base fictícia): este teste confere o mecanismo de avaliação, não os dados reais.
        linhas = [
            {"id": "q01", "conversa": "c01", "turno": "1", "tipo": "normal", "pergunta": "Que horas a UBS abre?", "esperado": "sete|7"},
            {"id": "q02", "conversa": "c01", "turno": "2", "tipo": "continuacao", "pergunta": "E o que eu levo?", "esperado": "foto|sus"},
            {"id": "q24", "conversa": "f01", "turno": "1", "tipo": "fora_escopo", "pergunta": "Quem ganhou o jogo de futebol ontem?", "esperado": ""},
            {"id": "q29", "conversa": "s01", "turno": "1", "tipo": "sem_resposta", "pergunta": "Qual é o endereço da UBS mais próxima da minha casa?", "esperado": ""},
        ]
        res = avaliar_llm.executar(LLM(), BaseStub(), linhas)
        por_id = {r["id"]: r for r in res}
        self.assertEqual(por_id["q01"]["acerto_auto"], 1)
        self.assertEqual(por_id["q02"]["acerto_auto"], 1)       # continuação achou a UBS pelo histórico
        self.assertEqual(por_id["q24"]["acerto_auto"], 1)       # futebol: guarda recusou sem chamar o LLM
        self.assertEqual(por_id["q24"]["motivo"], "sem_contexto")
        self.assertEqual(por_id["q29"]["acerto_auto"], 0)       # endereço: LLM falso "inventou", não abstém
        md = avaliar_llm.resumir(res)
        self.assertIn("falso", md)
        self.assertIn("Erros para análise", md)

    def test_erro_do_llm_nao_derruba_a_rodada(self):
        class LLMQuebrado:
            nome = "quebrado"
            def responder(self, system, historico, contexto):
                raise TimeoutError("tempo esgotado")

        linhas = [
            {"id": "a1", "conversa": "c1", "turno": "1", "tipo": "normal", "pergunta": "Que horas a UBS abre?", "esperado": "sete"},
            {"id": "a2", "conversa": "c2", "turno": "1", "tipo": "fora_escopo", "pergunta": "Quem ganhou o jogo ontem?", "esperado": ""},
        ]
        res = avaliar_llm.executar(LLMQuebrado(), BaseStub(), linhas)
        por_id = {r["id"]: r for r in res}
        self.assertEqual((por_id["a1"]["motivo"], por_id["a1"]["acerto_auto"]), ("erro", 0))
        self.assertIn("TimeoutError", por_id["a1"]["resposta"])
        self.assertEqual(por_id["a2"]["acerto_auto"], 1)  # a rodada seguiu: o fora do escopo nem chama o LLM

    def test_progresso_e_gravado_a_cada_pergunta(self):
        class LLM:
            nome = "falso"
            def responder(self, system, historico, contexto):
                return "sete horas"

        linhas = [{"id": f"p{i}", "conversa": f"c{i}", "turno": "1", "tipo": "normal",
                   "pergunta": "Que horas a UBS abre?", "esperado": "sete"} for i in range(3)]
        vistos = []
        avaliar_llm.executar(LLM(), BaseStub(), linhas, ao_terminar=lambda r: vistos.append(r["id"]))
        self.assertEqual(vistos, ["p0", "p1", "p2"])

    def test_retomar_so_pula_conversas_completas_e_sem_erro(self):
        linhas = [
            {"id": "q1", "conversa": "c1", "turno": "1"}, {"id": "q2", "conversa": "c1", "turno": "2"},
            {"id": "q3", "conversa": "c2", "turno": "1"}, {"id": "q4", "conversa": "c3", "turno": "1"},
        ]
        feitos = [
            {"id": "q1", "conversa": "c1", "motivo": "llm"}, {"id": "q2", "conversa": "c1", "motivo": "llm"},  # completa
            {"id": "q3", "conversa": "c2", "motivo": "erro"},                                                 # com erro
        ]                                                                                                     # c3: não feita
        self.assertEqual(avaliar_llm.conversas_completas(feitos, linhas), {"c1"})
        # conversa pela metade (falta o turno 2) também é refeita inteira, porque a continuação precisa da memória
        self.assertEqual(avaliar_llm.conversas_completas(feitos[:1], linhas), set())

    def test_acerto_manual_prevalece(self):
        r = {"acerto_auto": 0, "acerto_manual": "1"}
        self.assertTrue(avaliar_llm.acerto(r))
        self.assertFalse(avaliar_llm.acerto({"acerto_auto": 1, "acerto_manual": "0"}))
        self.assertTrue(avaliar_llm.acerto({"acerto_auto": 1, "acerto_manual": ""}))


class TesteTTS(unittest.TestCase):
    def test_gerar_e_resumir(self):
        with tempfile.TemporaryDirectory() as d:
            textos = ler_csv(TESTES / "respostas_tts.csv")
            tempos, planilha = avaliar_tts.gerar({"demo": DemoTTS()}, textos, Path(d))
            self.assertEqual(len(tempos), 10)
            self.assertEqual(len(planilha), 30)  # 10 respostas x 3 avaliadores
            self.assertEqual(len(list(Path(d).glob("*.wav"))), 10)
        for i, l in enumerate(planilha):
            l["naturalidade"], l["clareza"] = ("4", "5") if i % 2 else ("2", "3")
        planilha[0]["clareza"] = "9"  # nota inválida deve ser sinalizada
        md = avaliar_tts.resumir(planilha, tempos)
        self.assertIn("demo", md)
        self.assertIn("1 notas ainda vazias ou inválidas", md)

    def test_texto_falado_sem_digitos(self):
        _, planilha = avaliar_tts.gerar({"demo": DemoTTS()}, [{"id": "r1", "texto": "Custa R$ 50,00 até 15/03/2026."}],
                                        Path(tempfile.mkdtemp()))
        self.assertEqual(len(planilha), 3)


class TesteE2E(unittest.TestCase):
    def test_fluxo_com_modulos_falsos(self):
        with tempfile.TemporaryDirectory() as d:
            linhas = ler_csv(TESTES / "conversas_e2e.csv")
            for l in linhas:
                tom_wav(str(Path(d) / l["arquivo"]))
            res = avaliar_e2e.executar(DemoSTT(apagar_audio=False), DemoLLM(), BaseStub(), DemoTTS(), linhas, Path(d))
            self.assertEqual(len(res), 30)
            self.assertEqual(len(list(Path(d).glob("*.wav"))), 30)  # áudios de teste preservados
            md = avaliar_e2e.resumir(res)
            self.assertIn("10 conversas, 30 turnos", md)
            for etapa in avaliar_e2e.ETAPAS:
                self.assertIn(etapa, md)
        from config import SAIDA_DIR
        shutil.rmtree(SAIDA_DIR, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
