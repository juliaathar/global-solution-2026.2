"""Histórico desta sessão: cada interação com a IA vira uma linha e alimenta os gráficos."""
import pandas as pd
import streamlit as st

from web.ui import componentes as ui
from web.ui import graficos


def render() -> None:
    ui.cabecalho("Histórico desta visita", "O que você fez aqui hoje. Fica só neste navegador e some ao fechar.")
    hist = st.session_state.historico
    if not hist:
        ui.estado_vazio("Nada por aqui ainda.", "Faça uma pergunta, relate um problema ou envie uma foto.", "🕘")
        return
    fig1, fig2 = graficos.historico_sessao(hist)
    c1, c2 = st.columns(2)
    c1.plotly_chart(fig1, width="stretch")
    if fig2 is not None:
        c2.plotly_chart(fig2, width="stretch")
    df = pd.DataFrame(hist).rename(columns={"hora": "Hora", "tipo": "Tipo", "resultado": "Resultado",
                                            "latencia_ms": "Tempo (ms)", "categoria": "Assunto",
                                            "corrigido": "Cidadão corrigiu?"})
    df = df.astype(object).where(df.notna(), "")
    st.dataframe(df.iloc[::-1], hide_index=True, width="stretch")
    if st.button("Apagar histórico"):
        st.session_state.historico = []
        st.rerun()
