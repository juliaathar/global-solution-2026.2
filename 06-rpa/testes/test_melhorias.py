"""Testes das melhorias: retry por tipo de erro HTTP, snapshot velho, API simulada e sugestão de UBS."""
import sys
import tempfile
import threading
import unittest
from datetime import datetime
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "codigo"))

import config  # noqa: E402
import coleta_inmet  # noqa: E402
import coleta_web  # noqa: E402
import notificador  # noqa: E402


class _Resp:
    def __init__(self, codigo, texto="ok"):
        self.status_code, self.text, self.encoding = codigo, texto, "utf-8"

    def raise_for_status(self):
        if self.status_code >= 400:
            import requests
            raise requests.HTTPError(f"HTTP {self.status_code}")


class TestRetryPorTipoDeErro(unittest.TestCase):
    def setUp(self):
        self.p = mock.patch("coleta_web.permitido_por_robots", return_value=True)
        self.p.start()
        self.espera = config.ESPERA_ENTRE_REQUISICOES_S
        config.ESPERA_ENTRE_REQUISICOES_S = 0

    def tearDown(self):
        self.p.stop()
        config.ESPERA_ENTRE_REQUISICOES_S = self.espera

    def test_404_nao_repete(self):
        with mock.patch("coleta_web.requests.get", return_value=_Resp(404)) as g:
            with self.assertRaises(coleta_web.ErroColeta):
                coleta_web.baixar("http://x/y", tentativas=3, espera_base=0)
        self.assertEqual(g.call_count, 1)

    def test_500_repete_e_recupera(self):
        with mock.patch("coleta_web.requests.get", side_effect=[_Resp(503), _Resp(500), _Resp(200, "pagina")]) as g:
            self.assertEqual(coleta_web.baixar("http://x/y", tentativas=3, espera_base=0), "pagina")
        self.assertEqual(g.call_count, 3)

    def test_500_persistente_desiste_depois_das_tentativas(self):
        with mock.patch("coleta_web.requests.get", return_value=_Resp(500)) as g:
            with self.assertRaises(coleta_web.ErroColeta):
                coleta_web.baixar("http://x/y", tentativas=3, espera_base=0)
        self.assertEqual(g.call_count, 3)


class TestSnapshotVelho(unittest.TestCase):
    def test_avisa_quando_snapshot_ja_venceu(self):
        antes = config.OFFLINE
        config.OFFLINE = True
        try:
            with self.assertLogs("rpa.inmet", level="WARNING") as logs:
                coleta_inmet.coletar_avisos(agora=datetime(2030, 1, 1))
        finally:
            config.OFFLINE = antes
        self.assertIn("desatualizado", "".join(logs.output))

    def test_nao_avisa_quando_snapshot_ainda_vale(self):
        antes = config.OFFLINE
        config.OFFLINE = True
        try:
            with self.assertNoLogs("rpa.inmet", level="WARNING"):
                coleta_inmet.coletar_avisos(agora=datetime(2026, 11, 16, 12, 0))
        finally:
            config.OFFLINE = antes


class TestApiSimulada(unittest.TestCase):
    """POST real, por socket, contra a API simulada (o contrato que o front deve implementar)."""

    def test_post_do_protocolo_chega_na_api(self):
        import api_simulada
        servidor = api_simulada.criar_servidor(0)
        porta = servidor.server_address[1]
        t = threading.Thread(target=servidor.serve_forever, daemon=True)
        t.start()
        antes = (config.API_URL, config.EMAIL_ATIVO)
        config.API_URL, config.EMAIL_ATIVO = f"http://127.0.0.1:{porta}/protocolos", False
        notificador._entregues.clear()
        try:
            ok = notificador.enviar_com_retry("ELB-TESTE-1", 2, 0, dados={"urgencia": "alta"})
        finally:
            config.API_URL, config.EMAIL_ATIVO = antes
            servidor.shutdown()
            servidor.server_close()
        self.assertTrue(ok)
        self.assertEqual([p["protocolo"] for p in api_simulada.RECEBIDOS], ["ELB-TESTE-1"])

    def test_api_recusa_corpo_invalido(self):
        import api_simulada
        import urllib.request
        import urllib.error
        servidor = api_simulada.criar_servidor(0)
        porta = servidor.server_address[1]
        threading.Thread(target=servidor.serve_forever, daemon=True).start()
        try:
            req = urllib.request.Request(f"http://127.0.0.1:{porta}/protocolos", data=b"nao e json", method="POST")
            with self.assertRaises(urllib.error.HTTPError) as e:
                urllib.request.urlopen(req, timeout=3)
            self.assertEqual(e.exception.code, 400)
        finally:
            servidor.shutdown()
            servidor.server_close()


class TestSugestaoDeUBS(unittest.TestCase):
    def setUp(self):
        self.unidades = coleta_web.extrair_css(config.UBS_SNAPSHOT.read_text(encoding="utf-8"))

    def test_cada_unidade_citada_pelo_nome_e_encontrada(self):
        erros = []
        for u in self.unidades:
            bairro = u["nome"].removeprefix("UBS ")
            achada = coleta_web.sugerir_ubs(f"Onde fica a UBS do {bairro}? Preciso de atendimento.", self.unidades)
            if achada is None or achada["nome"] != u["nome"]:
                erros.append((u["nome"], achada and achada["nome"]))
        self.assertEqual(erros, [])  # 45 de 45

    def test_nome_mais_longo_vence(self):
        self.assertEqual(coleta_web.sugerir_ubs("a UBS Altos de Santana abre hoje?", self.unidades)["nome"], "UBS Altos de Santana")
        self.assertEqual(coleta_web.sugerir_ubs("a UBS Santana abre hoje?", self.unidades)["nome"], "UBS Santana")

    def test_sem_unidade_citada_devolve_none(self):
        self.assertIsNone(coleta_web.sugerir_ubs("onde tomar vacina perto daqui?", self.unidades))


try:
    import sklearn  # noqa: F401
    TEM_SKLEARN = True
except ImportError:
    TEM_SKLEARN = False


@unittest.skipUnless(TEM_SKLEARN, "scikit-learn não instalado (opcional)")
class TestComparacaoML(unittest.TestCase):
    def test_hibrido_preserva_regras_quando_elas_acertam(self):
        import avaliar_ml
        modelos = avaliar_ml.treinar(avaliar_ml.carregar_treino())
        texto = "Buraco perigoso na rua, houve acidente"
        self.assertEqual(avaliar_ml.prever_hibrido(modelos, texto), avaliar_ml.classificar(texto))

    def test_hibrido_nao_aceita_ml_pouco_confiante(self):
        import avaliar_ml
        modelos = avaliar_ml.treinar(avaliar_ml.carregar_treino())
        r = avaliar_ml.prever_hibrido(modelos, "Preciso falar com alguém sobre uma coisa")
        self.assertEqual(r["categoria"], "indefinido")


if __name__ == "__main__":
    unittest.main()
