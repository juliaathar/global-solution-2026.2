"""Testes do robô RPA. Rodar de 06-rpa/: python -m unittest discover -s testes -v"""
import csv
import sys
import os
import tempfile
from datetime import timedelta
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "codigo"))

import config  # noqa: E402
from classificador import classificar  # noqa: E402
import coleta_web  # noqa: E402
import coleta_inmet  # noqa: E402
import agendador  # noqa: E402
import smtplib  # noqa: E402
from unittest import mock  # noqa: E402
import main  # noqa: E402
from privacidade import mascarar  # noqa: E402
import coleta_noticias  # noqa: E402
from datetime import datetime  # noqa: E402
from deduplicacao import eh_duplicado, normalizar  # noqa: E402
from ingestao import ler_relatos  # noqa: E402
import notificador  # noqa: E402
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


class TestColetaWeb(unittest.TestCase):
    def setUp(self):
        self.doc = config.UBS_SNAPSHOT.read_text(encoding="utf-8")

    def test_css_e_xpath_extraem_o_mesmo(self):
        css, xp = coleta_web.extrair_css(self.doc), coleta_web.extrair_xpath(self.doc)
        self.assertGreaterEqual(len(css), 40)
        self.assertEqual(css, xp)
        self.assertTrue(all(u["endereco"] and u["horario"] for u in css))

    def test_rotulos_no_mesmo_paragrafo(self):
        u = next(u for u in coleta_web.extrair_css(self.doc) if u["nome"] == "UBS Novo Horizonte")
        self.assertNotIn("Horário", u["telefones"])
        self.assertTrue(u["horario"])

    def test_site_fora_do_ar_usa_snapshot(self):
        def falha(*a, **k):
            raise coleta_web.ErroColeta("simulado")
        orig, coleta_web.baixar = coleta_web.baixar, falha
        try:
            unidades, origem = coleta_web.coletar_ubs()
        finally:
            coleta_web.baixar = orig
        self.assertEqual(origem, "snapshot")
        self.assertGreaterEqual(len(unidades), 40)

    def test_html_mudou_seletor_vazio_usa_snapshot(self):
        orig = coleta_web.baixar
        coleta_web.baixar = lambda *a, **k: "<html><body><p>pagina nova</p></body></html>"
        try:
            unidades, origem = coleta_web.coletar_ubs()
        finally:
            coleta_web.baixar = orig
        self.assertEqual(origem, "snapshot")
        self.assertGreaterEqual(len(unidades), 40)

    def test_sugerir_ubs(self):
        unidades = coleta_web.extrair_css(self.doc)
        self.assertEqual(coleta_web.sugerir_ubs("onde fica a UBS do Jardim Paulista?", unidades)["nome"], "UBS Jardim Paulista")
        self.assertIsNone(coleta_web.sugerir_ubs("onde tomar vacina perto daqui?", unidades))


class TestInmet(unittest.TestCase):
    AGORA = datetime(2026, 11, 16, 12, 0)  # snapshot tem avisos de 07 a 18/11/2026

    def setUp(self):
        self.avisos = coleta_inmet.extrair_avisos(config.INMET_SNAPSHOT.read_text(encoding="utf-8"))

    def test_extrai_campos_do_cdata(self):
        self.assertEqual(len(self.avisos), 86)
        a = self.avisos[0]
        self.assertTrue(a["evento"] and a["severidade"] and a["inicio"] and a["fim"] and a["area"])

    def test_filtra_regiao_evento_e_vigencia(self):
        v = coleta_inmet.filtrar_vigentes(self.avisos, self.AGORA)
        self.assertGreater(len(v), 0)
        self.assertTrue(all("Vale do Paraíba Paulista" in a["area"] for a in v))
        self.assertTrue(all(a["inicio"] <= self.AGORA <= a["fim"] for a in v))
        self.assertEqual(coleta_inmet.filtrar_vigentes(self.avisos, datetime(2030, 1, 1)), [])

    def test_feed_fora_do_ar_usa_snapshot(self):
        def falha(*a, **k):
            raise coleta_web.ErroColeta("simulado")
        orig, coleta_inmet.baixar = coleta_inmet.baixar, falha
        try:
            _, origem = coleta_inmet.coletar_avisos(self.AGORA)
        finally:
            coleta_inmet.baixar = orig
        self.assertEqual(origem, "snapshot")

    def test_xml_invalido_usa_snapshot(self):
        orig, coleta_inmet.baixar = coleta_inmet.baixar, lambda *a, **k: "<rss><channel><item>"
        try:
            _, origem = coleta_inmet.coletar_avisos(self.AGORA)
        finally:
            coleta_inmet.baixar = orig
        self.assertEqual(origem, "snapshot")


class TestCrawlerNoticias(unittest.TestCase):
    def setUp(self):
        self.pag = [p.read_text(encoding="utf-8", errors="replace") for p in config.NOTICIAS_SNAPSHOTS]

    def test_css_e_xpath_extraem_o_mesmo(self):
        css, xp = coleta_noticias.extrair_css(self.pag[0]), coleta_noticias.extrair_xpath(self.pag[0])
        self.assertEqual(len(css), 12)
        self.assertEqual(css, xp)

    def test_pagina_falha_no_meio_mantem_o_coletado(self):
        chamadas = []

        def fake(url):
            chamadas.append(url)
            if len(chamadas) == 1:
                return self.pag[0]
            raise coleta_web.ErroColeta("simulado")
        noticias, info = coleta_noticias.rastrear(max_paginas=3, baixar_fn=fake)
        self.assertEqual((len(noticias), info["paginas"], info["falhas"], info["origem"]), (12, 1, 1, "web"))

    def test_respeita_limite_de_paginas(self):
        chamadas = []

        def fake(url):
            chamadas.append(url)
            return self.pag[len(chamadas) % 2]
        coleta_noticias.rastrear(max_paginas=2, baixar_fn=fake)
        self.assertEqual(len(chamadas), 2)

    def test_sem_noticias_novas_para_o_crawl(self):
        noticias, info = coleta_noticias.rastrear(max_paginas=5, baixar_fn=lambda u: self.pag[0])
        self.assertEqual(info["paginas"], 1)  # a 2ª página repete os mesmos ids

    def test_tudo_falha_usa_snapshot(self):
        def falha(u):
            raise coleta_web.ErroColeta("simulado")
        noticias, info = coleta_noticias.rastrear(max_paginas=2, baixar_fn=falha)
        self.assertEqual(info["origem"], "snapshot")
        self.assertEqual(len(noticias), 24)

    def test_filtro_por_tema_ignora_acento(self):
        n = [{"noticia_id": "1", "data": "", "titulo": "Iluminacao publica em novo bairro"},
             {"noticia_id": "2", "data": "", "titulo": "Copa de futebol"}]
        self.assertEqual([x["noticia_id"] for x in coleta_noticias.filtrar_por_tema(n)], ["1"])


class TestPrivacidade(unittest.TestCase):
    def test_mascara_cpf_email_telefone_cep(self):
        t, n = mascarar("CPF 123.456.789-09, tel (12) 99876-5432, joao@mail.com, CEP 12230-000")
        self.assertEqual(n, 4)
        for vazou in ("123.456", "99876", "joao@", "12230"):
            self.assertNotIn(vazou, t)

    def test_mascara_nome_dito_em_primeira_pessoa(self):
        self.assertIn("[NOME]", mascarar("Me chamo Maria Souza, buraco na Rua Sete")[0])

    def test_nao_mascara_numero_de_rua_nem_frase_comum(self):
        for txt in ("Buraco na Rua Sete, 411", "Alagamento na Av. Brasil, 1500", "Sou a favor de consertar o poste"):
            self.assertEqual(mascarar(txt), (txt, 0))

    def test_texto_pessoal_nao_chega_ao_banco_nem_a_revisao(self):
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            (d / "e.csv").write_text(
                "id,texto\n"
                "P1,Buraco perigoso na Rua Sete. Ligar 12 99876-5432 ou joao@mail.com\n"
                "P2,Preciso de ajuda com uma coisa 123.456.789-09 que nao sei explicar\n", encoding="utf-8")
            velho = (config.SAIDA, config.BANCO, config.LOG, config.RELATORIO, config.REVISAO)
            config.SAIDA, config.BANCO, config.LOG = d, d / "p.db", d / "l.log"
            config.RELATORIO, config.REVISAO = d / "r.json", d / "rev.csv"
            try:
                r = main.executar(d / "e.csv")
            finally:
                config.SAIDA, config.BANCO, config.LOG, config.RELATORIO, config.REVISAO = velho
            self.assertEqual(r["resumo"]["dados_pessoais_mascarados"], 3)
            saida = (d / "rev.csv").read_text(encoding="utf-8") + (d / "r.json").read_text(encoding="utf-8")
            for vazou in ("99876", "joao@", "123.456"):
                self.assertNotIn(vazou, saida)


class TestClassificadorAmpliado(unittest.TestCase):
    def test_vocabulario_novo_e_palavra_inteira(self):
        self.assertEqual(classificar("A rua está toda esburacada")["categoria"], "buraco")
        self.assertEqual(classificar("O que fazer com a subsidiária do bairro")["categoria"], "indefinido")  # 'ubs' dentro de palavra

    def test_alagamento_e_alta_exceto_sinal_preventivo(self):
        self.assertEqual(classificar("O bueiro entupiu e a agua subiu")["urgencia"], "alta")
        self.assertEqual(classificar("A boca de lobo está cheia de folhas e a água não escoa")["urgencia"], "media")

    def test_amostra_independente_nao_regride(self):
        import csv
        linhas = list(csv.DictReader(open(config.RAIZ / "dados_sinteticos" / "amostra_independente.csv", encoding="utf-8")))
        acertos = sum(classificar(r["texto"])["categoria"] == r["categoria_real"] for r in linhas)
        self.assertGreaterEqual(acertos / len(linhas), 0.9)


class TestEnriquecimento(unittest.TestCase):
    def test_urgencia_do_inmet_vai_para_o_banco(self):
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            (d / "e.csv").write_text("id,texto\nA1,O bueiro da Rua Sete esta entupido e a agua inunda a rua\n", encoding="utf-8")
            velho = (config.SAIDA, config.BANCO, config.LOG, config.RELATORIO, config.REVISAO)
            config.SAIDA, config.BANCO, config.LOG = d, d / "p.db", d / "l.log"
            config.RELATORIO, config.REVISAO = d / "r.json", d / "rev.csv"
            orig = main.Enriquecedor.aviso_inmet
            main.Enriquecedor.aviso_inmet = lambda self, c: "Inmet: Tempestade (Perigo) em teste"
            try:
                r = main.executar(d / "e.csv")
            finally:
                main.Enriquecedor.aviso_inmet = orig
                config.SAIDA, config.BANCO, config.LOG, config.RELATORIO, config.REVISAO = velho
            import sqlite3
            con = sqlite3.connect(d / "p.db")
            urg = con.execute("SELECT urgencia FROM protocolos").fetchone()[0]
            con.close()
            self.assertEqual(urg, "alta")
            self.assertEqual(r["protocolos"][0]["alerta_inmet"], "Inmet: Tempestade (Perigo) em teste")


class TestEmail(unittest.TestCase):
    DADOS = {"categoria": "alagamento", "urgencia": "alta", "confianca": 1.0,
             "encaminhamento": "", "alerta_inmet": "Inmet: Tempestade (Perigo) em Vale"}

    def setUp(self):
        self.antes = (config.SMTP_USUARIO, config.SMTP_SENHA, config.EMAIL_DESTINO, config.EMAIL_ATIVO,
                      config.API_URL, config.EMAIL_URGENCIAS)
        config.SMTP_USUARIO, config.SMTP_SENHA = "robo@exemplo.com", "senha-de-teste"
        config.EMAIL_DESTINO, config.EMAIL_ATIVO, config.API_URL = "gestor@exemplo.com", True, ""
        config.EMAIL_URGENCIAS = ("alta",)
        notificador._entregues.clear()

    def tearDown(self):
        (config.SMTP_USUARIO, config.SMTP_SENHA, config.EMAIL_DESTINO, config.EMAIL_ATIVO,
         config.API_URL, config.EMAIL_URGENCIAS) = self.antes

    def test_envia_email_com_login_e_starttls(self):
        with mock.patch("notificador.smtplib.SMTP") as smtp:
            notificador.enviar("ELB-1", self.DADOS)
        srv = smtp.return_value.__enter__.return_value
        srv.starttls.assert_called_once()
        srv.login.assert_called_once_with("robo@exemplo.com", "senha-de-teste")
        msg = srv.send_message.call_args[0][0]
        self.assertEqual(msg["To"], "gestor@exemplo.com")
        self.assertIn("ELB-1", msg["Subject"])
        self.assertIn("Inmet", msg.get_content())

    def test_email_nao_leva_texto_do_cidadao(self):
        msg = notificador.montar_email("ELB-1", {**self.DADOS, "texto": "Ligar 12 99876-5432", "id": "R1"})
        self.assertNotIn("99876", msg.as_string())

    def test_sem_config_ou_urgencia_baixa_nao_envia(self):
        with mock.patch("notificador.smtplib.SMTP") as smtp:
            notificador.enviar("ELB-1", {**self.DADOS, "urgencia": "media"})
            config.EMAIL_ATIVO = False
            notificador.enviar("ELB-2", self.DADOS)
            notificador.enviar("ELB-3")  # sem dados: só simula
        smtp.assert_not_called()

    def test_falha_do_smtp_vira_retry_e_nao_quebra(self):
        with mock.patch("notificador.smtplib.SMTP", side_effect=OSError("rede fora")) as smtp:
            ok = enviar_com_retry("ELB-1", 3, 0, dados=self.DADOS)
        self.assertFalse(ok)
        self.assertEqual(smtp.call_count, 3)

    def test_senha_recusada_nao_repete(self):
        with mock.patch("notificador.smtplib.SMTP") as smtp:
            smtp.return_value.__enter__.return_value.login.side_effect = smtplib.SMTPAuthenticationError(535, b"recusada")
            ok = enviar_com_retry("ELB-1", 3, 0, dados=self.DADOS)
        self.assertFalse(ok)
        self.assertEqual(smtp.call_count, 1)

    def test_retry_nao_reenvia_canal_ja_entregue(self):
        config.API_URL = "http://api.local/protocolos"
        chamadas = {"api": 0}

        def api_ok(_p):
            chamadas["api"] += 1
        with mock.patch("notificador._enviar_api", api_ok),                 mock.patch("notificador.smtplib.SMTP", side_effect=[OSError("1a falha"), mock.DEFAULT]):
            ok = enviar_com_retry("ELB-9", 3, 0, dados=self.DADOS)
        self.assertTrue(ok)
        self.assertEqual(chamadas["api"], 1)  # a API não foi chamada de novo na 2ª tentativa

    def test_senha_nao_aparece_no_log_de_erro(self):
        with mock.patch("notificador.smtplib.SMTP", side_effect=OSError("rede fora")),                 self.assertLogs("rpa.notificador", level="WARNING") as logs:
            enviar_com_retry("ELB-1", 1, 0, dados=self.DADOS)
        self.assertNotIn("senha-de-teste", "".join(logs.output))


def _isolar(d):
    """Aponta saída, banco e histórico para uma pasta temporária; devolve o estado antigo para restaurar."""
    campos = ("SAIDA", "BANCO", "LOG", "RELATORIO", "REVISAO", "HISTORICO", "LOCK", "ENTRADA", "USAR_NOTICIAS")
    antigo = {c: getattr(config, c) for c in campos}
    config.SAIDA, config.BANCO, config.LOG = d, d / "p.db", d / "l.log"
    config.RELATORIO, config.REVISAO = d / "r.json", d / "rev.csv"
    config.HISTORICO, config.LOCK = d / "hist.jsonl", d / "agendador.lock"
    return antigo


def _restaurar(antigo):
    for c, v in antigo.items():
        setattr(config, c, v)


class TestAgendador(unittest.TestCase):
    def test_parse_horarios(self):
        self.assertEqual(agendador.parse_horarios("18:00, 08:00,08:00"), ["08:00", "18:00"])
        for ruim in ("", "25:00", "8h", "08:60"):
            with self.assertRaises(agendador.ErroAgendamento):
                agendador.parse_horarios(ruim)

    def test_proxima_execucao_hoje_e_amanha(self):
        h = ["08:00", "18:00"]
        self.assertEqual(agendador.proxima_execucao(datetime(2026, 11, 17, 7, 0), h), datetime(2026, 11, 17, 8, 0))
        self.assertEqual(agendador.proxima_execucao(datetime(2026, 11, 17, 8, 0), h), datetime(2026, 11, 17, 18, 0))
        self.assertEqual(agendador.proxima_execucao(datetime(2026, 11, 17, 19, 0), h), datetime(2026, 11, 18, 8, 0))
        self.assertEqual(agendador.proxima_execucao(datetime(2026, 12, 31, 23, 0), h), datetime(2027, 1, 1, 8, 0))

    def test_busca_manual_registra_historico(self):
        with tempfile.TemporaryDirectory() as d:
            antigo = _isolar(Path(d))
            orig = agendador.main.executar
            agendador.main.executar = lambda entrada: {"resumo": {"protocolos": 3}, "protocolos": []}
            try:
                reg = agendador.executar_busca("manual")
            finally:
                agendador.main.executar = orig
                _restaurar(antigo)
            self.assertEqual((reg["status"], reg["gatilho"], reg["resumo"]["protocolos"]), ("ok", "manual", 3))
            self.assertEqual(len((Path(d) / "hist.jsonl").read_text(encoding="utf-8").splitlines()), 1)
            self.assertFalse((Path(d) / "agendador.lock").exists())  # lock liberado

    def test_busca_simultanea_e_ignorada(self):
        with tempfile.TemporaryDirectory() as d:
            antigo = _isolar(Path(d))
            try:
                with agendador.Lock():
                    reg = agendador.executar_busca("agendado")
            finally:
                _restaurar(antigo)
            self.assertEqual(reg["status"], "ignorada")

    def test_lock_esquecido_e_removido(self):
        with tempfile.TemporaryDirectory() as d:
            antigo = _isolar(Path(d))
            velho = config.LOCK_VALIDADE_S
            config.LOCK.write_text("pid antigo")
            os.utime(config.LOCK, (0, 0))  # lock de 1970
            try:
                with agendador.Lock():
                    pass
            finally:
                config.LOCK_VALIDADE_S = velho
                _restaurar(antigo)

    def test_erro_na_busca_nao_derruba_o_servico(self):
        with tempfile.TemporaryDirectory() as d:
            antigo = _isolar(Path(d))
            orig = agendador.main.executar

            def quebra(entrada):
                raise RuntimeError("falha inesperada")
            agendador.main.executar = quebra
            try:
                reg = agendador.executar_busca("agendado")
            finally:
                agendador.main.executar = orig
                _restaurar(antigo)
            self.assertEqual(reg["status"], "erro")
            self.assertFalse((Path(d) / "agendador.lock").exists())

    def test_servir_executa_nos_horarios_com_relogio_falso(self):
        relogio = {"t": datetime(2026, 11, 17, 7, 59, 0)}
        dormidos = []

        def dormir(seg):
            dormidos.append(seg)
            relogio["t"] += timedelta(seconds=seg)
        buscas = []
        orig = agendador.executar_busca
        agendador.executar_busca = lambda gatilho, com_noticias=True: buscas.append((gatilho, relogio["t"])) or {}
        try:
            feitas = agendador.servir(["08:00", "18:00"], agora_fn=lambda: relogio["t"], dormir_fn=dormir, max_execucoes=3)
        finally:
            agendador.executar_busca = orig
        self.assertEqual(feitas, 3)
        self.assertEqual([b[0] for b in buscas], ["agendado"] * 3)
        self.assertEqual([b[1].strftime("%d %H:%M") for b in buscas], ["17 08:00", "17 18:00", "18 08:00"])
        self.assertTrue(all(s <= 30 for s in dormidos))


class TestBuscasRepetidas(unittest.TestCase):
    def test_segunda_busca_nao_cria_protocolo_para_copias(self):
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            (d / "e.csv").write_text(
                "id,texto\n"
                "A1,Buraco perigoso na Rua Sete com risco de acidente\n"
                "A2,Buraco perigoso na Rua Sete com risco de acidente\n", encoding="utf-8")
            antigo = _isolar(d)
            try:
                r1 = main.executar(d / "e.csv")["resumo"]
                r2 = main.executar(d / "e.csv")["resumo"]
            finally:
                _restaurar(antigo)
            self.assertEqual((r1["protocolos"], r1["duplicados"]), (1, 1))
            self.assertEqual((r2["protocolos"], r2["duplicados"], r2["ja_processados"]), (0, 1, 1))


if __name__ == "__main__":
    unittest.main()
