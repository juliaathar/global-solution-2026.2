import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from interfaces import Trecho  # noqa: E402
from llm import Assistente  # noqa: E402
from llm.assistente import MSG_EMERGENCIA, MSG_SEM_CONTEXTO, eh_emergencia, parece_continuacao  # noqa: E402
from llm.base_stub import BaseStub  # noqa: E402


class LLMEspiao:
    nome = "espiao"

    def __init__(self):
        self.chamadas = []

    def responder(self, system, historico, contexto):
        self.chamadas.append((list(historico), list(contexto)))
        return "resposta do llm"


class TestGuardas(unittest.TestCase):
    def setUp(self):
        self.llm = LLMEspiao()
        self.a = Assistente(self.llm, BaseStub())

    def test_sem_contexto_nao_chama_llm(self):
        r = self.a.perguntar("Quem ganhou o jogo de futebol ontem?")
        self.assertEqual(r, MSG_SEM_CONTEXTO)
        self.assertEqual(self.a.ultimo_motivo, "sem_contexto")
        self.assertEqual(self.llm.chamadas, [])

    def test_com_contexto_chama_llm(self):
        self.assertEqual(self.a.perguntar("Que horas a UBS abre?"), "resposta do llm")
        self.assertEqual(self.a.ultimo_motivo, "llm")
        self.assertEqual(len(self.llm.chamadas), 1)

    def test_emergencia_nao_chama_llm(self):
        r = self.a.perguntar("Socorro, meu pai está com dor no peito!")
        self.assertEqual(r, MSG_EMERGENCIA)
        self.assertEqual(self.a.ultimo_motivo, "emergencia")
        self.assertEqual(self.llm.chamadas, [])

    def test_emergencia_sem_acento_e_caixa(self):
        self.assertTrue(eh_emergencia("EMERGÊNCIA aqui"))
        self.assertFalse(eh_emergencia("Onde fica o CRAS?"))

    def test_emergencias_que_a_primeira_lista_nao_pegava(self):
        for frase in ("Meu vizinho está passando mal", "Tem alguém sendo agredido na rua",
                      "Meu filho está engasgado", "Ele está tendo uma convulsão"):
            self.assertTrue(eh_emergencia(frase), frase)

    def test_perguntas_normais_nao_sao_emergencia(self):
        for frase in ("Que horas a UBS abre?", "Como relato lixo acumulado na calçada?",
                      "Preciso do cartão do SUS para ir à UBS?", "O poste da minha rua está apagado"):
            self.assertFalse(eh_emergencia(frase), frase)

    def test_guarda_pode_ser_desligada(self):
        a = Assistente(self.llm, BaseStub(), exigir_contexto=False)
        self.assertEqual(a.perguntar("Quem ganhou o jogo?"), "resposta do llm")


class TestFugaDaGuarda(unittest.TestCase):
    """Uma pergunta solta, depois de uma pergunta do tema, não pode herdar o contexto anterior."""

    def test_deteccao_de_continuacao(self):
        for f in ("E o que eu levo?", "e ela fecha que horas", "Mas isso gera protocolo?",
                  "Então onde eu vou?", "Preciso levar algo lá?", "E eu preciso de comprovante?"):
            self.assertTrue(parece_continuacao(f), f)
        for f in ("Obrigado! Me conta uma piada!", "Conta uma piada.", "Qual é a capital da França?",
                  "Agora me dá uma receita de bolo.", "Escreve um poema sobre o mar.",
                  "Obrigado. E quem ganhou o jogo ontem?"):
            self.assertFalse(parece_continuacao(f), f)

    def test_pergunta_solta_depois_de_pergunta_do_tema_cai_na_guarda(self):
        llm = LLMEspiao()
        a = Assistente(llm, BaseStub())
        a.perguntar("Que horas a UBS abre?")
        for pergunta in ("Obrigado! Me conta uma piada!", "Qual é a capital da França?"):
            self.assertEqual(a.perguntar(pergunta), MSG_SEM_CONTEXTO)
            self.assertEqual(a.ultimo_motivo, "sem_contexto")
        self.assertEqual(len(llm.chamadas), 1)  # só a primeira pergunta chegou ao LLM

    def test_continuacao_legitima_continua_funcionando(self):
        llm = LLMEspiao()
        a = Assistente(llm, BaseStub())
        a.perguntar("Que horas a UBS abre?")
        a.perguntar("E o que eu levo?")
        self.assertEqual(a.ultimo_motivo, "llm")
        self.assertEqual(len(llm.chamadas), 2)

    def test_fala_com_cara_de_continuacao_mas_de_outro_assunto_cai_na_guarda(self):
        """'E me conta uma piada?' começa com 'e', mas não divide nenhuma palavra com a conversa."""
        llm = LLMEspiao()
        a = Assistente(llm, BaseStub())
        a.perguntar("Que horas a UBS abre?")
        for pergunta in ("E me conta uma piada?", "E o dólar, quanto está hoje?",
                         "Obrigado. E quem ganhou o jogo ontem?"):
            self.assertEqual(a.perguntar(pergunta), MSG_SEM_CONTEXTO, pergunta)
        self.assertEqual(len(llm.chamadas), 1)

    def test_palavra_comum_como_sobre_nao_casa_com_o_corpus(self):
        """'sobre' aparece no texto do CRAS; um pedido de poema sobre o mar não pode herdar esse trecho."""
        a = Assistente(LLMEspiao(), BaseStub())
        self.assertEqual(a.perguntar("Escreve um poema sobre o mar."), MSG_SEM_CONTEXTO)

    def test_continuacoes_do_conjunto_de_teste_seguem_como_continuacao(self):
        casos = [("Que horas a UBS abre?", "E o que eu levo?"),
                 ("Em quais dias a UBS atende?", "E que horas ela fecha?"),
                 ("Para que serve o CRAS?", "E o que eu preciso levar lá?"),
                 ("Como faço a segunda via do RG?", "E o que eu levo?"),
                 ("Tem um buraco na minha rua. Como eu aviso?", "E isso gera algum número para acompanhar?")]
        for primeira, segunda in casos:
            llm = LLMEspiao()
            a = Assistente(llm, BaseStub())
            a.perguntar(primeira)
            a.perguntar(segunda)
            self.assertEqual(a.ultimo_motivo, "llm", segunda)
            self.assertEqual(len(llm.chamadas), 2, segunda)


class TestContinuacaoSoComPalavrasGenericas(unittest.TestCase):
    """O exemplo do próprio enunciado: "e onde eu faço isso?" depois de uma pergunta do tema."""

    def _assistente_depois_de(self, pergunta_anterior):
        from interfaces import Mensagem
        a = Assistente(LLMEspiao(), BaseStub())
        a.historico = [Mensagem("user", pergunta_anterior), Mensagem("assistant", "Certo.")]
        return a

    def test_onde_eu_faco_isso_e_continuacao(self):
        # "faço" e "fazer" não compartilham as 3 primeiras letras; só tem palavra genérica, logo é continuação
        a = self._assistente_depois_de("Quais documentos preciso levar para fazer o Cadastro Único?")
        self.assertTrue(a._eh_continuacao("E onde eu faço isso?"))

    def test_outras_continuacoes_so_com_palavras_genericas(self):
        a = self._assistente_depois_de("Como peço a limpeza de um bueiro entupido?")
        for f in ("E qual o horário?", "E qual o telefone?", "E isso é gratuito?"):
            self.assertTrue(a._eh_continuacao(f), f)

    def test_troca_de_assunto_com_substantivo_novo_continua_sendo_barrada(self):
        a = self._assistente_depois_de("Quais documentos preciso levar para fazer o Cadastro Único?")
        for f in ("E me conta uma piada?", "E quem ganhou o jogo ontem?", "E o dólar, quanto está hoje?"):
            self.assertFalse(a._eh_continuacao(f), f)

    def test_a_pergunta_do_enunciado_chega_ao_llm_com_o_assunto_anterior(self):
        a = self._assistente_depois_de("Que horas a UBS abre?")
        a.perguntar("E onde eu faço isso?")
        self.assertEqual(a.ultimo_motivo, "llm")  # buscou com a pergunta anterior e achou contexto


class TestMemoria(unittest.TestCase):
    def test_continuacao_reaproveita_pergunta_anterior_na_busca(self):
        llm = LLMEspiao()
        a = Assistente(llm, BaseStub())
        a.perguntar("Que horas a UBS abre?")
        # "E o que eu levo?" sozinha não acha nada; com o histórico, acha a UBS.
        self.assertEqual(BaseStub().buscar("E o que eu levo?"), [])
        a.perguntar("E o que eu levo?")
        self.assertEqual(len(llm.chamadas), 2)
        self.assertEqual(a.ultimo_motivo, "llm")

    def test_historico_enviado_ao_llm_inclui_turnos_anteriores(self):
        llm = LLMEspiao()
        a = Assistente(llm, BaseStub())
        a.perguntar("Que horas a UBS abre?")
        a.perguntar("E o que eu levo?")
        historico, _ = llm.chamadas[1]
        self.assertEqual([m.papel for m in historico], ["user", "assistant", "user"])

    def test_guarda_tambem_entra_no_historico(self):
        a = Assistente(LLMEspiao(), BaseStub())
        a.perguntar("Quem ganhou o jogo?")
        self.assertEqual([m.papel for m in a.historico], ["user", "assistant"])

    def test_memoria_limitada(self):
        llm = LLMEspiao()
        a = Assistente(llm, BaseStub(), k=1)
        for _ in range(20):
            a.perguntar("Que horas a UBS abre?")
        self.assertLessEqual(len(llm.chamadas[-1][0]), 11)

    def test_limpar(self):
        a = Assistente(LLMEspiao(), BaseStub())
        a.perguntar("Que horas a UBS abre?")
        a.limpar()
        self.assertEqual(a.historico, [])


if __name__ == "__main__":
    unittest.main()
