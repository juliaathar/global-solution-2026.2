"""Avisos da casa: alerta visual quando o OuviAí (pasta 05) reconhece campainha ou batida na porta.

Para quem tem deficiência auditiva. A tela confere a API a cada 3 s (st.fragment) e mostra o último
alerta em destaque, com ícone, texto e horário. A classe "ambiente" não alerta.
"""
import os
from datetime import datetime
from html import escape

import streamlit as st

from web.providers import api_cliente as api
from web.state import sessao
from web.ui import componentes as ui
from web.ui import graficos


ATUALIZAR_S = float(os.getenv("IOT_ATUALIZAR_S", "3")) or None  # 0 desliga a atualização automática


@st.fragment(run_every=ATUALIZAR_S)
def _painel_ao_vivo() -> None:
    try:
        eventos = api.eventos_som(50)
    except api.ErroAPI as e:
        ui.erro_api(e, "Não consegui ver os avisos da casa")
        return
    alertas = [e for e in eventos if e["virou_alerta"]]
    if not alertas:
        ui.estado_vazio("Tudo calmo por aqui.",
                        "Quando tocarem a campainha ou baterem na porta, o aviso aparece nesta tela.", "🔕")
    else:
        ultimo = alertas[0]
        quando = datetime.fromisoformat(ultimo["criado_em"])
        segundos = (datetime.now() - quando).total_seconds()
        recente = segundos < 120
        ha = "agora mesmo" if segundos < 60 else f"há {int(segundos // 60)} min" if segundos < 3600 else f"às {quando:%H:%M}"
        ui.aviso_casa(ultimo["icone"], ultimo["mensagem"],
                      f"{ha} · {quando:%H:%M:%S} · certeza {ultimo['confianca']:.0%} · {ultimo['dispositivo']}", recente)
        if ultimo["id"] != st.session_state.ultimo_alerta_visto:
            st.session_state.ultimo_alerta_visto = ultimo["id"]
            st.toast(f"{ultimo['icone']} {ultimo['mensagem']}", icon="🔔")
            sessao.registrar("alerta sonoro", ultimo["classe"], None)
    if eventos:
        with st.expander("Últimos sons ouvidos"):
            itens = []
            for e in eventos[:10]:
                h = datetime.fromisoformat(e["criado_em"]).strftime("%H:%M:%S")
                marca = "🔔 virou aviso" if e["virou_alerta"] else f"🔕 ignorado: {e['motivo']}"
                itens.append(f"<li><span>{e['icone']} {escape(e['mensagem'])}</span>"
                             f"<span class='q'>{h} · {e['confianca']:.0%} · {escape(marca)}</span></li>")
            ui._html(f"<ul class='elb-lista'>{''.join(itens)}</ul>")


def render() -> None:
    ui.cabecalho("Avisos da casa", "Para quem não ouve a porta: o celular reconhece a campainha e a batida e o aviso "
                                   "aparece aqui. Nenhum áudio sai do celular.")
    _painel_ao_vivo()
    with st.expander("🧪 Testar sem o celular (simulador)"):
        st.caption("Manda um evento igual ao que a ponte do Edge Impulse (05-iot/codigo/ponte_alertas.py) envia.")
        c1, c2, c3 = st.columns([1.2, 1.2, 1], vertical_alignment="bottom")
        classe = c1.selectbox("Som", ["campainha", "batida_porta", "ambiente"],
                              format_func={"campainha": "🔔 Campainha", "batida_porta": "🚪 Batida na porta",
                                           "ambiente": "🔈 Som do ambiente"}.get)
        conf = c2.slider("Confiança do modelo", 0.0, 1.0, 0.92, 0.01)
        if c3.button("Enviar evento", width="stretch"):
            try:
                r, _ = api.enviar_evento_som(classe, conf)
                (st.success if r["virou_alerta"] else st.info)(f"{r['icone']} {r['mensagem']}: {r['motivo']}")
            except api.ErroAPI as e:
                ui.erro_api(e)


def grafico() -> None:
    """Usado no painel do gestor."""
    try:
        fig = graficos.eventos_som(api.eventos_som(500))
    except api.ErroAPI as e:
        ui.erro_api(e, "Sem dados do IoT")
        return
    if fig is None:
        ui.estado_vazio("Nenhum som recebido do OuviAí ainda.", "", "🔕")
    else:
        st.plotly_chart(fig, width="stretch")
