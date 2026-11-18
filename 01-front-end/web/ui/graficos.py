"""Gráficos Plotly reutilizáveis. Paleta Okabe-Ito (segura para daltonismo) e rótulos em texto nas barras,
para que a informação não dependa só da cor."""
import pandas as pd
import plotly.express as px

OKABE_ITO = ["#0E6A8A", "#E69F00", "#009E73", "#CC79A7", "#56B4E9", "#D55E00", "#F0E442", "#17283A"]
COR_URGENCIA = {"Alta": "#B3261E", "Média": "#E0A100", "Baixa": "#2E7D4F"}
ROTULO_URGENCIA = {"alta": "Alta", "media": "Média", "baixa": "Baixa"}
ROTULO_CATEGORIA = {
    "buraco": "Buraco", "iluminacao": "Iluminação", "lixo": "Lixo e entulho", "calcada": "Calçada",
    "alagamento": "Alagamento", "servico_saude": "Saúde", "indefinido": "Outro",
}
# Centro aproximado das regiões de São José dos Campos (para o mapa de calor por região)
REGIOES = {
    "Centro": (-23.1857, -45.8863), "Norte": (-23.1480, -45.8980), "Sul": (-23.2450, -45.8900),
    "Leste": (-23.1900, -45.8100), "Oeste": (-23.2060, -45.9420), "Sudeste": (-23.2200, -45.8520),
}
FONTE = "Atkinson Hyperlegible, system-ui, sans-serif"
LAYOUT = dict(margin=dict(l=12, r=12, t=56, b=12), font=dict(family=FONTE, size=15, color="#17283A"),
              title_font=dict(family=FONTE, size=18, color="#17283A"), legend_title_text="",
              paper_bgcolor="#FFFFFF", plot_bgcolor="#FFFFFF", hoverlabel=dict(font_family=FONTE),
              xaxis=dict(gridcolor="#E6ECF1", zeroline=False), yaxis=dict(gridcolor="#E6ECF1", zeroline=False))


def preparar(ocorrencias: list[dict]) -> pd.DataFrame:
    df = pd.DataFrame(ocorrencias)
    if df.empty:
        return df
    df["Categoria"] = df["categoria"].map(ROTULO_CATEGORIA).fillna(df["categoria"])
    df["Urgência"] = df["urgencia"].map(ROTULO_URGENCIA).fillna(df["urgencia"])
    df["Origem"] = df["origem"].map({"app": "App (cidadão)", "robo_rpa": "Robô RPA"}).fillna(df["origem"])
    df["criado_em"] = pd.to_datetime(df["criado_em"])
    df["Dia"] = df["criado_em"].dt.date
    return df


def barras_categoria_urgencia(df: pd.DataFrame):
    contagem = df.groupby(["Categoria", "Urgência"]).size().reset_index(name="Protocolos")
    fig = px.bar(contagem, x="Protocolos", y="Categoria", color="Urgência", orientation="h", text="Protocolos",
                 color_discrete_map=COR_URGENCIA, category_orders={"Urgência": ["Alta", "Média", "Baixa"]},
                 title="Protocolos por assunto e urgência")
    fig.update_layout(**LAYOUT, yaxis_title="", barmode="stack")
    return fig


def linha_no_tempo(df: pd.DataFrame):
    """Por dia; se tudo couber em menos de 2 dias, por hora (senão a linha vira um ponto só)."""
    curto = (df["criado_em"].max() - df["criado_em"].min()) < pd.Timedelta(days=2)
    passo, fmt, titulo = ("h", "%d/%m %Hh", "Protocolos abertos por hora") if curto else ("D", "%d/%m", "Protocolos abertos por dia")
    serie = (df.assign(Periodo=df["criado_em"].dt.floor(passo)).groupby(["Periodo", "Origem"]).size()
             .reset_index(name="Protocolos").sort_values("Periodo"))
    serie["Quando"] = serie["Periodo"].dt.strftime(fmt)
    fig = px.line(serie, x="Quando", y="Protocolos", color="Origem", markers=True, symbol="Origem", text="Protocolos",
                  color_discrete_sequence=OKABE_ITO, title=titulo)
    fig.update_traces(textposition="top center")
    fig.update_layout(**LAYOUT, xaxis_title="", xaxis_type="category")
    return fig


def mapa_regioes(df: pd.DataFrame):
    com_regiao = df[df["regiao"].isin(REGIOES)]
    if com_regiao.empty:
        return None
    agg = com_regiao.groupby("regiao").agg(Protocolos=("protocolo", "count"),
                                           Alta=("urgencia", lambda s: int((s == "alta").sum()))).reset_index()
    agg["lat"] = agg["regiao"].map(lambda r: REGIOES[r][0])
    agg["lon"] = agg["regiao"].map(lambda r: REGIOES[r][1])
    agg["Rótulo"] = agg.apply(lambda r: f"{r['regiao']}: {r['Protocolos']} ({r['Alta']} alta)", axis=1)
    fig = px.scatter_map(agg, lat="lat", lon="lon", size="Protocolos", color="Alta", text="Rótulo",
                         color_continuous_scale=["#56B4E9", "#D55E00"],
                         range_color=[0, max(1, int(agg["Alta"].max()))], size_max=40, zoom=10.3,
                         center={"lat": -23.20, "lon": -45.88}, map_style="open-street-map",
                         hover_data={"lat": False, "lon": False}, title="Onde estão os pedidos (por região)")
    fig.update_traces(textposition="top right", textfont=dict(size=14, color="#111"))
    fig.update_layout(**LAYOUT, height=430, coloraxis_colorbar_title="Urgência alta")
    return fig


def eventos_som(eventos: list[dict]):
    df = pd.DataFrame(eventos)
    if df.empty:
        return None
    df["Classe"] = df["classe"].map({"campainha": "Campainha", "batida_porta": "Batida na porta",
                                     "ambiente": "Ambiente"})
    df["Resultado"] = df["virou_alerta"].map({True: "Virou alerta", False: "Ignorado"})
    contagem = df.groupby(["Classe", "Resultado"]).size().reset_index(name="Eventos")
    fig = px.bar(contagem, x="Classe", y="Eventos", color="Resultado", text="Eventos", barmode="group",
                 pattern_shape="Resultado", color_discrete_map={"Virou alerta": "#0E6A8A", "Ignorado": "#9AA7B3"},
                 pattern_shape_map={"Virou alerta": "", "Ignorado": "/"},
                 title="Sons detectados pelo OuviAí")
    fig.update_layout(**LAYOUT, xaxis_title="")
    fig.update_yaxes(tickformat="d", rangemode="tozero", dtick=1 if contagem["Eventos"].max() <= 10 else None)
    return fig


def historico_sessao(historico: list[dict]):
    df = pd.DataFrame(historico)
    if df.empty:
        return None, None
    contagem = df.groupby(["tipo", "resultado"]).size().reset_index(name="Interações")
    fig1 = px.bar(contagem, x="tipo", y="Interações", color="resultado", text="Interações",
                  color_discrete_sequence=OKABE_ITO, title="Interações desta sessão")
    fig1.update_layout(**LAYOUT, xaxis_title="")
    fig1.update_yaxes(tickformat="d", dtick=1 if contagem["Interações"].max() <= 10 else None)
    lat = df.dropna(subset=["latencia_ms"]).reset_index(drop=True)
    fig2 = None
    if not lat.empty:
        lat["Interação"] = [f"{i + 1}. {t}" for i, t in enumerate(lat["tipo"])]
        fig2 = px.bar(lat, x="Interação", y="latencia_ms", color="tipo", text="latencia_ms",
                      color_discrete_sequence=OKABE_ITO, title="Tempo de resposta de cada interação (ms)")
        fig2.update_layout(**LAYOUT, yaxis_title="ms", xaxis_title="", showlegend=False)
    return fig1, fig2
