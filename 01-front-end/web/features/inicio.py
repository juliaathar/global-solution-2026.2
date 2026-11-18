"""Página inicial do cidadão: as três coisas que dá para fazer, com a mais comum em destaque."""
import streamlit as st

from web.state import navegacao
from web.ui import componentes as ui

ATALHOS = {
    "relatar": ("📢", "Avisar a prefeitura de um problema",
                "Buraco, poste apagado, lixo, calçada quebrada ou alagamento. Você recebe um número de protocolo.",
                "Relatar um problema"),
    "perguntar": ("💬", "Tirar uma dúvida",
                  "UBS, vacina, Cadastro Único, poda de árvore. Escreva ou fale.", "Perguntar"),
    "avisos": ("🔔", "Avisos da casa",
               "Veja na tela quando tocarem a campainha ou baterem na porta.", "Ver avisos"),
}


def _atalho(chave: str) -> None:
    icone, titulo, texto, botao = ATALHOS[chave]
    with st.container(border=True, key=f"atalho_{chave}"):
        st.markdown(f"<div class='ico' aria-hidden='true'>{icone}</div>", unsafe_allow_html=True)
        st.markdown(f"### {titulo}")
        st.markdown(texto)
        st.page_link(navegacao.pagina(chave), label=botao, icon=":material/arrow_forward:")


def render() -> None:
    ui.cabecalho("Olá! O que você precisa hoje?",
                 "Serviços da prefeitura de São José dos Campos, do jeito mais simples: escrevendo, falando ou com uma foto.")
    esq, dir_ = st.columns([1.35, 1], gap="medium")
    with esq:
        _atalho("relatar")
    with dir_:
        _atalho("perguntar")
        _atalho("avisos")
    st.caption("🔒 Nada vira protocolo sem a sua confirmação. Em emergência ligue 192 (SAMU), 193 (Bombeiros) "
               "ou 190 (Polícia).")
