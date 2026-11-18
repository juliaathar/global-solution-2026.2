import pandas as pd
import streamlit as st

from web.providers import api_visao

AVISO_FIXO = ("**Triagem apenas.** A presença de fissura na imagem não define a gravidade do dano "
              "nem a segurança da estrutura. Uma pessoa qualificada deve avaliar o local.")


def _resultado_imagem(r: dict):
    if r["inspecao_recomendada"]:
        st.error("⚠️ Possível fissura: inspeção recomendada")
    else:
        st.success("✅ Nenhuma fissura detectada nesta imagem")
    c1, c2 = st.columns(2)
    c1.metric("Confiança do modelo", f"{r['confianca'] * 100:.1f}%")
    c2.metric("Probabilidade de fissura", f"{r['probabilidade_fissura'] * 100:.1f}%")
    st.progress(r["probabilidade_fissura"], text=f"P(fissura) com limiar em {r['limiar']:.2f}")
    if r["confianca"] < 0.7:
        st.warning("Confiança baixa: o resultado é incerto. Considere nova foto com boa luz e sem sombra.")
    st.caption(f"Processado em {r['latencia_ms']} ms")


def _aba_imagem(limiar: float):
    arq = st.file_uploader("Foto da fachada, parede ou calçada (JPG ou PNG, até 5 MB)", type=["jpg", "jpeg", "png"], key="vc_img")
    if arq is None:
        st.info("Envie uma foto para analisar.")
        return
    col_img, col_res = st.columns(2)
    col_img.image(arq, use_container_width=True)
    with col_res:
        try:
            with st.spinner("Analisando a imagem..."):
                r = api_visao.classificar_imagem(arq, limiar)
        except api_visao.ErroAPI as e:
            st.error(str(e))
            return
        _resultado_imagem(r)


def _aba_video(limiar: float):
    arq = st.file_uploader("Vídeo curto para simular monitoramento (MP4, AVI, MOV, até 50 MB)", type=["mp4", "avi", "mov", "mkv"], key="vc_vid")
    passo = st.slider("Analisar 1 a cada N quadros", 1, 30, 5)
    if arq is None:
        st.info("Envie um vídeo curto para analisar.")
        return
    if not st.button("Analisar vídeo"):
        return
    try:
        with st.spinner("Processando o vídeo..."):
            r = api_visao.classificar_video(arq, passo, limiar)
    except api_visao.ErroAPI as e:
        st.error(str(e))
        return
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Quadros analisados", r["quadros_analisados"])
    c2.metric("Com alerta", f"{r['percentual_alertas']}%", f"{r['quadros_com_alerta']} quadros", delta_color="off")
    c3.metric("Latência média", f"{r['latencia_media_ms']} ms")
    c4.metric("FPS", r["fps_processamento"])
    st.caption(f"Resolução original: {r['resolucao_original']}")
    df = pd.DataFrame(r["quadros"]).set_index("tempo_s")
    st.line_chart(df["probabilidade_fissura"])
    alertas = df[df["alerta"]]
    if alertas.empty:
        st.success("Nenhum quadro com alerta de inspeção.")
    else:
        st.error(f"⚠️ {len(alertas)} quadros com possível fissura, nos tempos (s): "
                 + ", ".join(str(t) for t in alertas.index[:15]) + ("..." if len(alertas) > 15 else ""))


def render():
    st.header("Danos em fachadas e calçadas")
    st.warning(AVISO_FIXO)
    with st.sidebar:
        limiar = st.slider("Limiar de inspeção", 0.1, 0.9, 0.45, 0.05,
                           help="Padrão 0,45, escolhido na validação (recall >= 0,99). Mais baixo = detecta mais fissuras, com mais falsos alarmes.")
    tab_img, tab_vid = st.tabs(["Imagem", "Vídeo"])
    with tab_img:
        _aba_imagem(limiar)
    with tab_vid:
        _aba_video(limiar)
