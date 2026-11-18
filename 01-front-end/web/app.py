"""Interface EloBairro. Rodar a partir de 01-front-end:  streamlit run web/app.py

Duas visões: Cidadão (perguntar, relatar, avisos da casa) e Gestor (painel, fotos de danos).
A interface nunca chama o LLM nem os modelos: tudo passa pela API (web/providers).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import streamlit as st  # noqa: E402

from web.features import avisos_casa, historico, inicio, painel_gestor, perguntar, relatar, visao  # noqa: E402
from web.providers import api_cliente as api  # noqa: E402
from web.state import navegacao, sessao  # noqa: E402
from web.ui import componentes as ui  # noqa: E402

st.set_page_config(page_title="EloBairro", page_icon="🏘️", layout="wide", initial_sidebar_state="auto",
                   menu_items={"About": "EloBairro: serviços públicos do bairro por voz, texto e foto. FIAP GS 2026.2."})
sessao.iniciar()


def barra_lateral() -> None:
    with st.sidebar:
        st.html("<div class='elb-marca'><span class='elb-placa' aria-hidden='true'>E</span><b>EloBairro</b></div>")
        st.segmented_control("Quem está usando?", ["Cidadão", "Gestor"], key="perfil",
                             help="O gestor vê o painel com todos os pedidos.")
        if not st.session_state.perfil:  # o controle permite desmarcar; volta para o padrão
            st.session_state.perfil = "Cidadão"
        st.markdown("### Para ler melhor")
        st.toggle("Letra grande", key="letra_grande")
        st.toggle("Alto contraste", key="alto_contraste")
        st.toggle("Botão para ouvir as respostas", key="ler_em_voz_alta")
        st.markdown("### Sistema")
        try:
            s = api.saude()
            ui.status_sistema(True, "Sistema no ar")
            fora = [m for m, v in s["modulos"].items() if v != "ok"]
            if fora:
                st.caption("Desligado nesta máquina: " + ", ".join(fora))
            st.caption(f"Classificação de relatos: {s['llm']}")
        except api.ErroAPI as e:
            ui.status_sistema(False, "Sistema fora do ar")
            st.caption(str(e))
        with st.expander("🔒 Privacidade"):
            st.markdown("- Seu áudio e sua foto não são guardados.\n- Telefone, CPF, e-mail e nome são tirados do texto.\n"
                        "- Nada vira protocolo sem a sua confirmação.\n- Em emergência ligue 192 (SAMU), 193 (Bombeiros) "
                        "ou 190 (Polícia).")


barra_lateral()
ui.aplicar_estilo(st.session_state.letra_grande, st.session_state.alto_contraste)

# Uma página por vez (st.navigation): só a página aberta roda. Assim a atualização automática dos
# avisos da casa não interrompe quem está preenchendo um relato em outra página.
P = navegacao.PAGINAS
P.update({
    "inicio": st.Page(inicio.render, title="Início", icon=":material/home:", url_path="inicio", default=True),
    "perguntar": st.Page(perguntar.render, title="Perguntar", icon=":material/chat:", url_path="perguntar"),
    "relatar": st.Page(relatar.render, title="Relatar problema", icon=":material/campaign:", url_path="relatar"),
    "avisos": st.Page(avisos_casa.render, title="Avisos da casa", icon=":material/notifications:", url_path="avisos"),
    "historico": st.Page(historico.render, title="Histórico", icon=":material/history:", url_path="historico"),
    # o gestor tem as próprias páginas (outros endereços): ao trocar de perfil, a página do perfil anterior
    # deixa de existir no menu e o app abre a primeira página do novo perfil
    "avisos_g": st.Page(avisos_casa.render, title="Avisos da casa", icon=":material/notifications:",
                        url_path="avisos-gestor"),
    "historico_g": st.Page(historico.render, title="Histórico", icon=":material/history:", url_path="historico-gestor"),
    "painel": st.Page(painel_gestor.render, title="Painel", icon=":material/dashboard:", url_path="painel"),
    "danos": st.Page(visao.render, title="Danos em fotos", icon=":material/photo_camera:", url_path="danos"),
})
MENU = {"Cidadão": ["inicio", "perguntar", "relatar", "avisos", "historico"],
        "Gestor": ["painel", "danos", "avisos_g", "historico_g"]}
paginas = [P[k] for k in MENU[st.session_state.perfil]]  # sem a página padrão na lista, a primeira abre
st.navigation(paginas, position="top").run()
