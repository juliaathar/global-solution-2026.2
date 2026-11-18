"""Visão do gestor: indicadores, filtros, gráficos Plotly, mapa por região e revisão humana dos protocolos."""
import pandas as pd
import streamlit as st

from web.features import avisos_casa
from web.providers import api_cliente as api
from web.ui import componentes as ui
from web.ui import graficos

STATUS_OPCOES = {"aberto": "📬 Aberto", "em_analise": "🔎 Em análise", "resolvido": "✔️ Resolvido"}


def filtrar(df: pd.DataFrame, categorias, urgencias, regioes, origens, status) -> pd.DataFrame:
    """Aplica os filtros escolhidos; lista vazia = sem filtro naquele campo."""
    for col, sel in (("Categoria", categorias), ("Urgência", urgencias), ("regiao", regioes),
                     ("Origem", origens), ("status", status)):
        if sel:
            df = df[df[col].isin(sel)]
    return df


def _filtros(df: pd.DataFrame):
    with st.container(border=True):
        c1, c2, c3, c4, c5 = st.columns(5)
        cats = c1.multiselect("Assunto", sorted(df["Categoria"].unique()), placeholder="Todos")
        urgs = c2.multiselect("Urgência", ["Alta", "Média", "Baixa"], placeholder="Todas")
        regs = c3.multiselect("Região", sorted(df["regiao"].unique()), placeholder="Todas")
        origs = c4.multiselect("Origem", sorted(df["Origem"].unique()), placeholder="Todas")
        sts = c5.multiselect("Situação", list(STATUS_OPCOES), format_func=STATUS_OPCOES.get, placeholder="Todas")
    return cats, urgs, regs, origs, sts


def _revisao(df: pd.DataFrame) -> None:
    st.markdown("#### Revisão humana")
    st.caption("O que a IA não teve certeza fica esperando uma pessoa. Mude a situação quando conferir.")
    pend = df[df["status"] == "em_analise"]
    if pend.empty:
        st.caption("Nenhum protocolo aguardando revisão com os filtros atuais.")
    c1, c2, c3 = st.columns([2, 2, 1])
    opcoes = list(pend["protocolo"]) or list(df["protocolo"].head(50))
    prot = c1.selectbox("Protocolo", opcoes, help="Os que estão em análise aparecem primeiro.")
    novo = c2.selectbox("Nova situação", list(STATUS_OPCOES), format_func=STATUS_OPCOES.get)
    if c3.button("Salvar", width="stretch", disabled=not opcoes):
        try:
            api.mudar_status(prot, novo)
            ui.aviso("sucesso", f"{prot} agora está como {STATUS_OPCOES[novo]}")
        except api.ErroAPI as e:
            ui.erro_api(e)


def render() -> None:
    topo1, topo2 = st.columns([3, 1], vertical_alignment="bottom")
    with topo1:
        ui.cabecalho("Painel do bairro", "Pedidos abertos pelos moradores no app e pelo robô de triagem. "
                                         "Dados de demonstração.")
    if topo2.button("Importar do robô RPA", width="stretch"):
        try:
            r, _ = api.importar_rpa()
            ui.aviso("sucesso", f"{r['importados']} protocolos novos do robô", f"{r['ja_existiam']} já estavam no painel.")
        except api.ErroAPI as e:
            ui.erro_api(e, "Não consegui carregar o relatório do robô")
    try:
        with st.spinner("Carregando protocolos..."):
            df = graficos.preparar(api.protocolos())
    except api.ErroAPI as e:
        ui.erro_api(e, "Não consegui carregar o painel")
        return
    if df.empty:
        ui.estado_vazio("Ainda não há protocolos.", "Registre um relato na visão do cidadão ou carregue os do robô RPA.", "📋")
        return

    sel = _filtros(df)
    f = filtrar(df, *sel)
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Protocolos", len(f))
    k2.metric("🔴 Urgentes em aberto", int(((f["urgencia"] == "alta") & (f["status"] != "resolvido")).sum()))
    k3.metric("🔎 Esperando revisão", int((f["status"] == "em_analise").sum()))
    k4.metric("✔️ Resolvidos", int((f["status"] == "resolvido").sum()))
    if f.empty:
        ui.estado_vazio("Nenhum protocolo com esses filtros.", "Tire algum filtro para ver mais.")
        return

    g1, g2 = st.columns(2)
    g1.plotly_chart(graficos.barras_categoria_urgencia(f), width="stretch")
    g2.plotly_chart(graficos.linha_no_tempo(f), width="stretch")
    mapa = graficos.mapa_regioes(f)
    if mapa is None:
        st.caption("🗺️ Mapa: nenhum protocolo com região informada nesses filtros (os do robô RPA não têm região).")
    else:
        st.plotly_chart(mapa, width="stretch")
        st.caption("Círculos no centro aproximado de cada região; tamanho = quantidade, cor = quantos são urgentes.")

    with st.expander(f"📄 Tabela ({len(f)} protocolos)"):
        tabela = f[["protocolo", "Origem", "Categoria", "Urgência", "regiao", "status", "confianca", "resumo",
                    "criado_em"]].rename(columns={"protocolo": "Protocolo", "regiao": "Região", "status": "Situação",
                                                  "confianca": "Certeza", "resumo": "Resumo", "criado_em": "Criado em"})
        st.dataframe(tabela, hide_index=True, width="stretch")
        st.download_button("Baixar CSV", tabela.to_csv(index=False).encode("utf-8"), "protocolos.csv", "text/csv")
    _revisao(f)
    st.divider()
    st.markdown("#### Avisos sonoros nas casas")
    avisos_casa.grafico()
