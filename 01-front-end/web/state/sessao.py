"""Estado da sessão (st.session_state) num lugar só, com nomes e valores iniciais documentados."""
from datetime import datetime

import streamlit as st

PADRAO = {
    "perfil": "Cidadão",            # Cidadão | Gestor
    "letra_grande": False,
    "alto_contraste": False,
    "ler_em_voz_alta": False,
    "chat": [],                     # [{role, content, fontes}]
    "proposta": None,               # proposta da IA aguardando confirmação do cidadão
    "foto_resultado": None,         # resultado da visão computacional para o relato atual
    "meus_protocolos": [],          # protocolos criados nesta sessão
    "historico": [],                # cada interação com a IA: alimenta os gráficos da aba Histórico
    "ultimo_alerta_visto": 0,       # id do último alerta sonoro já mostrado
    "versao_form": 0,               # troca a chave do formulário para limpá-lo depois do envio
}


def iniciar() -> None:
    for chave, valor in PADRAO.items():
        if chave not in st.session_state:
            st.session_state[chave] = list(valor) if isinstance(valor, list) else valor


def registrar(tipo: str, resultado: str, latencia_ms: float | None = None, **extra) -> None:
    """Guarda uma interação (pergunta, relato, foto, voz, alerta) para o histórico e os gráficos."""
    st.session_state.historico.append({"hora": datetime.now().strftime("%H:%M:%S"), "tipo": tipo,
                                       "resultado": resultado, "latencia_ms": latencia_ms, **extra})


def limpar_relato() -> None:
    st.session_state.proposta = None
    st.session_state.foto_resultado = None
    st.session_state.versao_form += 1
