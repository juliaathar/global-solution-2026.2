"""Testes da API (pytest). Rodar a partir de 01-front-end:  python -m pytest testes -v"""
import json

import pytest
import requests
from fastapi.testclient import TestClient

from api.core import config
from api.main import app
from api.providers import llm_provider

cliente = TestClient(app)
RELATO = "Tem um buraco enorme na Rua das Flores, 120, quase causou acidente com uma moto"


def _confirmar(p: dict, **extra) -> dict:
    corpo = {"confirmado": True, "texto_mascarado": p["texto_mascarado"], "categoria": p["categoria"],
             "urgencia": p["urgencia"], "confianca": p["confianca"], "metodo": p["metodo"], "regiao": p["regiao"]}
    return cliente.post("/relatos/confirmar", json={**corpo, **extra})


# ---------- saúde, CORS e validação de entrada ----------

def test_saude_lista_modulos():
    r = cliente.get("/saude")
    assert r.status_code == 200
    assert r.json()["modulos"]["relatos"] == "ok"


def test_cors_aceita_so_a_origem_do_front():
    ok = cliente.options("/saude", headers={"Origin": "http://localhost:8501", "Access-Control-Request-Method": "GET"})
    ruim = cliente.options("/saude", headers={"Origin": "http://site-malicioso.com", "Access-Control-Request-Method": "GET"})
    assert ok.headers.get("access-control-allow-origin") == "http://localhost:8501"
    assert "access-control-allow-origin" not in ruim.headers


@pytest.mark.parametrize("corpo, campo", [
    ({}, "texto"),                                       # obrigatório
    ({"texto": "buraco"}, "texto"),                      # curto demais
    ({"texto": "x" * 501}, "texto"),                     # longo demais
    ({"texto": "          oi          "}, "texto"),      # só espaços não contam
    ({"texto": RELATO, "regiao": "Marte"}, "regiao"),    # valor fora da lista
])
def test_relato_invalido_da_422_em_portugues(corpo, campo):
    r = cliente.post("/relatos/analisar", json=corpo)
    assert r.status_code == 422
    erros = r.json()["detail"]
    assert any(e["campo"] == campo for e in erros)
    assert all("String should" not in e["mensagem"] for e in erros)


# ---------- IA: proposta, falha do LLM e resposta inválida ----------

def test_sem_llm_usa_regras_do_robo_e_mascara_dados_pessoais():
    r = cliente.post("/relatos/analisar", json={"texto": RELATO + ". Meu telefone 12 99876-5432", "regiao": "Sul"})
    p = r.json()
    assert r.status_code == 200
    assert p["metodo"] == "regras"
    assert p["categoria"] == "buraco" and p["urgencia"] == "alta"
    assert "99876" not in p["texto_mascarado"] and "[TELEFONE]" in p["texto_mascarado"]
    assert p["dados_pessoais_mascarados"] == 1


def test_llm_fora_do_ar_cai_para_regras(monkeypatch):
    monkeypatch.setattr(config, "LLM_PROVIDER", "groq")
    monkeypatch.setattr(config, "LLM_API_KEY", "chave-falsa")

    def fora_do_ar(*a, **k):
        raise requests.ConnectionError("sem rede")
    monkeypatch.setattr(llm_provider.requests, "post", fora_do_ar)
    p = cliente.post("/relatos/analisar", json={"texto": "Poste apagado na rua da escola, tudo escuro à noite"}).json()
    assert p["metodo"] == "regras" and p["categoria"] == "iluminacao"
    assert any("não respondeu" in a for a in p["avisos"])


def test_llm_timeout_cai_para_regras(monkeypatch):
    monkeypatch.setattr(config, "LLM_PROVIDER", "openai")
    monkeypatch.setattr(config, "LLM_API_KEY", "chave-falsa")
    monkeypatch.setattr(llm_provider.requests, "post", lambda *a, **k: (_ for _ in ()).throw(requests.Timeout()))
    p = cliente.post("/relatos/analisar", json={"texto": "Lixo e entulho acumulado na esquina da praça"}).json()
    assert p["metodo"] == "regras" and p["categoria"] == "lixo"


@pytest.mark.parametrize("bruto", [
    "Claro! A categoria é buraco.",                                        # sem JSON
    '{"categoria": "foguete", "urgencia": "alta", "resumo": "algo"}',      # categoria inexistente
    '{"categoria": "buraco"}',                                             # campos faltando
    '{"categoria": "buraco", "urgencia": "alta", "resumo": "' + "x" * 300 + '"}',  # resumo grande demais
])
def test_resposta_invalida_do_llm_e_rejeitada(bruto):
    with pytest.raises(llm_provider.ErroLLM):
        llm_provider.interpretar(bruto)


def test_resposta_valida_do_llm_com_cerca_markdown():
    e = llm_provider.interpretar('```json\n{"categoria": "alagamento", "urgencia": "alta", "resumo": "Rua alagada"}\n```')
    assert e.categoria == "alagamento"


def test_llm_valido_e_usado_e_regra_de_risco_prevalece(monkeypatch):
    monkeypatch.setattr(llm_provider, "disponivel", lambda: True)
    monkeypatch.setattr(llm_provider, "_chamar", lambda m: json.dumps(
        {"categoria": "buraco", "urgencia": "baixa", "resumo": "Buraco perigoso na rua"}))
    p = cliente.post("/relatos/analisar", json={"texto": RELATO}).json()
    assert p["metodo"] == "llm" and p["confianca"] == 0.9
    assert p["urgencia"] == "alta"  # o texto fala de acidente: a regra de segurança vence o LLM


def test_texto_ambiguo_pede_revisao_humana():
    p = cliente.post("/relatos/analisar", json={"texto": "Queria reclamar de uma coisa que aconteceu ontem aqui"}).json()
    assert p["categoria"] == "indefinido" and p["precisa_revisao"] is True


def test_foto_com_fissura_vira_calcada():
    p = cliente.post("/relatos/analisar", json={"texto": "Olha o estado disso aqui na frente de casa",
                                               "foto": {"probabilidade_fissura": 0.93, "inspecao_recomendada": True}}).json()
    assert p["categoria"] == "calcada"
    assert any("fissura" in a for a in p["avisos"])


# ---------- human-in-the-loop e protocolo ----------

def test_confirmar_exige_sim_explicito():
    p = cliente.post("/relatos/analisar", json={"texto": "Bueiro entupido na Rua Sete, água subindo"}).json()
    assert _confirmar(p, confirmado=False).status_code == 422


def test_confirmar_gera_protocolo_no_banco_do_robo_e_nao_duplica():
    p = cliente.post("/relatos/analisar", json={"texto": "Calçada quebrada na frente do mercado municipal, cadeirante não passa",
                                               "regiao": "Norte"}).json()
    r1 = _confirmar(p)
    assert r1.status_code == 201
    prot = r1.json()
    assert prot["novo"] and prot["protocolo"].startswith("ELB-")
    assert "156" in prot["encaminhamento"]
    r2 = _confirmar(p).json()  # o mesmo relato de novo
    assert r2["novo"] is False and r2["protocolo"] == prot["protocolo"]
    lista = cliente.get("/protocolos", params={"regiao": "Norte"}).json()
    assert any(o["protocolo"] == prot["protocolo"] for o in lista)


def test_correcao_do_cidadao_fica_registrada():
    p = cliente.post("/relatos/analisar", json={"texto": "Problema sério com a lâmpada da praça central"}).json()
    prot = _confirmar(p, categoria="iluminacao", corrigido_pelo_cidadao=True).json()
    o = [x for x in cliente.get("/protocolos").json() if x["protocolo"] == prot["protocolo"]][0]
    assert o["metodo"].endswith("correcao_cidadao")


# ---------- contrato do robô RPA (06) ----------

def test_contrato_do_robo_201_e_400():
    assert cliente.post("/protocolos", json={"protocolo": "ELB-20261117-09999"}).json() == {"recebido": "ELB-20261117-09999"}
    assert cliente.post("/protocolos", content=b"nao e json").status_code == 400
    assert cliente.post("/protocolos", json={"outro": 1}).status_code == 400


def test_importa_relatorio_do_robo():
    r = cliente.post("/protocolos/importar-rpa")
    assert r.status_code == 200 and r.json()["importados"] + r.json()["ja_existiam"] > 0


def test_gestor_muda_status_e_404():
    prot = cliente.get("/protocolos", params={"limite": 1}).json()[0]["protocolo"]
    assert cliente.patch(f"/protocolos/{prot}/status", json={"status": "resolvido"}).status_code == 200
    assert cliente.patch("/protocolos/ELB-NAO-EXISTE/status", json={"status": "resolvido"}).status_code == 404
    assert cliente.patch(f"/protocolos/{prot}/status", json={"status": "sumiu"}).status_code == 422


# ---------- IoT (05) ----------

def test_iot_ambiente_e_baixa_confianca_nao_alertam_e_repeticao_e_ignorada():
    assert cliente.post("/iot/eventos", json={"classe": "ambiente", "confianca": 0.99}).json()["virou_alerta"] is False
    assert cliente.post("/iot/eventos", json={"classe": "campainha", "confianca": 0.5}).json()["virou_alerta"] is False
    a = cliente.post("/iot/eventos", json={"classe": "batida_porta", "confianca": 0.95}).json()
    assert a["virou_alerta"] and a["vibracao_ms"]
    assert cliente.post("/iot/eventos", json={"classe": "batida_porta", "confianca": 0.97}).json()["virou_alerta"] is False


def test_iot_token(monkeypatch):
    monkeypatch.setattr(config, "IOT_TOKEN", "segredo")
    assert cliente.post("/iot/eventos", json={"classe": "campainha", "confianca": 0.9}).status_code == 401
    r = cliente.post("/iot/eventos", json={"classe": "campainha", "confianca": 0.9},
                     headers={"X-Dispositivo-Token": "segredo"})
    assert r.status_code == 201


def test_painel_resumo():
    r = cliente.get("/painel/resumo").json()
    assert r["total"] >= 1 and "buraco" in r["por_categoria"]


def test_enderecos_diferentes_nao_viram_duplicado():
    a = cliente.post("/relatos/analisar", json={"texto": "Poste apagado na Rua das Acácias, 45, fica escuro à noite",
                                               "regiao": "Oeste"}).json()
    pa = _confirmar(a).json()
    b = cliente.post("/relatos/analisar", json={"texto": "Poste apagado na Rua das Palmeiras, 88, fica escuro à noite",
                                               "regiao": "Oeste"}).json()
    assert b["duplicado_de"] is None
    assert _confirmar(b).json()["protocolo"] != pa["protocolo"]
