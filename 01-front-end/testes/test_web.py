"""Testes da interface: validação no front, filtros, gráficos e comportamento com a API fora do ar."""
from pathlib import Path

import pandas as pd
from streamlit.testing.v1 import AppTest

from web.features.painel_gestor import filtrar
from web.features.relatar import validar
from web.ui import graficos

APP = str(Path(__file__).resolve().parents[1] / "web" / "app.py")


class _Foto:
    def __init__(self, tipo, tamanho):
        self.type, self.size = tipo, tamanho


def test_validacao_do_formulario():
    assert validar("", None) == ["Conte o que aconteceu. Esse campo é obrigatório."]
    assert "pelo menos" in validar("buraco", None)[0]
    assert "passou de 500" in validar("x" * 501, None)[0]
    assert "JPG ou PNG" in validar("Poste apagado na rua da escola", _Foto("image/gif", 10))[0]
    assert "5 MB" in validar("Poste apagado na rua da escola", _Foto("image/png", 6 * 1024 * 1024))[0]
    assert validar("Poste apagado na rua da escola", _Foto("image/jpeg", 1000)) == []


def _ocorrencias():
    base = {"origem": "app", "canal": "texto", "confianca": 0.9, "status": "aberto", "metodo": "regras",
            "resumo": "", "criado_em": "2026-11-17T10:00:00", "probabilidade_fissura": None, "alerta_inmet": ""}
    return graficos.preparar([
        {**base, "protocolo": "ELB-1", "categoria": "buraco", "urgencia": "alta", "regiao": "Sul"},
        {**base, "protocolo": "ELB-2", "categoria": "lixo", "urgencia": "baixa", "regiao": "Centro"},
        {**base, "protocolo": "ELB-3", "categoria": "buraco", "urgencia": "media", "regiao": "Centro",
         "origem": "robo_rpa", "criado_em": "2026-11-18T09:00:00"},
    ])


def test_dois_filtros_combinados():
    df = _ocorrencias()
    assert len(filtrar(df, ["Buraco"], [], [], [], [])) == 2
    assert len(filtrar(df, ["Buraco"], [], ["Centro"], [], [])) == 1
    assert len(filtrar(df, [], ["Alta"], [], ["Robô RPA"], [])) == 0


def test_graficos_plotly():
    df = _ocorrencias()
    assert graficos.barras_categoria_urgencia(df).data
    assert graficos.linha_no_tempo(df).data
    assert graficos.mapa_regioes(df).data
    assert graficos.mapa_regioes(df[df["regiao"] == "Marte"]) is None
    f1, f2 = graficos.historico_sessao([{"hora": "10:00:00", "tipo": "relato", "resultado": "ok", "latencia_ms": 120}])
    assert f1.data and f2.data


def test_app_abre_com_api_fora_do_ar_sem_quebrar(monkeypatch):
    from web.providers import api_cliente
    monkeypatch.setattr(api_cliente, "API_URL", "http://127.0.0.1:9")  # porta fechada
    api_cliente.saude.clear()
    at = AppTest.from_file(APP, default_timeout=30).run()
    assert not at.exception
    assert any("Não foi possível falar com o sistema" in c.value for c in at.caption)
