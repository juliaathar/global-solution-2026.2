"""Perguntar sobre serviços públicos, por texto ou voz. Respostas do motor RAG (03) com as fontes."""
import streamlit as st

from web.providers import api_cliente as api
from web.state import sessao
from web.ui import componentes as ui

EXEMPLOS = ["Que horas abre a UBS?", "Como pedir a poda de uma árvore?",
            "O que levo para fazer o Cadastro Único?"]


def _mostrar_resposta(r: dict) -> None:
    if r.get("bloqueada"):
        ui.aviso("atencao", "Não posso ajudar com esse pedido", r["resposta"])
    elif r.get("abstencao"):
        ui.aviso("info", "Não encontrei nas fontes oficiais", r["resposta"])
    elif r.get("esclarecimento"):
        ui.aviso("info", "Preciso de mais detalhes", r["resposta"])
    else:
        st.markdown(r["resposta"])
    if r.get("fontes"):
        with st.expander(f"📚 Fontes oficiais ({len(r['fontes'])})"):
            for f in r["fontes"]:
                st.markdown(f"- [{f['titulo']}]({f['url']}) (consultado em {f['data_consulta']})")


def _ler(texto: str) -> None:
    try:
        with st.spinner("Preparando o áudio..."):
            a, _ = api.falar(texto)
        ui.tocar_audio(a["audio_base64"], a["formato_audio"])
    except api.ErroAPI as e:
        ui.aviso("atencao", "Leitura em voz alta indisponível", str(e))


def _resultado_tipo(r: dict) -> str:
    return ("bloqueada" if r.get("bloqueada") else "sem fonte" if r.get("abstencao")
            else "pediu detalhes" if r.get("esclarecimento") else "respondida")


def _perguntar_texto(pergunta: str) -> None:
    historico = [{"role": m["role"], "content": m["content"][:2000]} for m in st.session_state.chat]
    st.session_state.chat.append({"role": "user", "content": pergunta})
    try:
        with st.spinner("Procurando nas fontes oficiais..."):
            r, ms = api.perguntar(pergunta, historico)
    except api.ErroAPI as e:
        st.session_state.chat.append({"role": "assistant", "content": f"⛔ {e}", "erro": True})
        sessao.registrar("pergunta", "erro", None)
        return
    st.session_state.chat.append({"role": "assistant", "content": r["resposta"], "dados": r})
    sessao.registrar("pergunta", _resultado_tipo(r), ms)


def _aba_texto() -> None:
    if not st.session_state.chat:
        st.markdown("**Comece por uma destas ou escreva a sua:**")
        for i, (col, ex) in enumerate(zip(st.columns(len(EXEMPLOS)), EXEMPLOS)):
            if col.button(ex, key=f"exemplo_{i}", width="stretch"):
                _perguntar_texto(ex)
                st.rerun()
    for i, m in enumerate(st.session_state.chat):
        with st.chat_message(m["role"], avatar="🧑" if m["role"] == "user" else "🏘️"):
            if m.get("dados"):
                _mostrar_resposta(m["dados"])
                if st.session_state.ler_em_voz_alta and st.button("🔊 Ouvir resposta", key=f"ouvir_{i}"):
                    _ler(m["content"])
            else:
                st.markdown(m["content"])
    pergunta = st.chat_input("Escreva sua pergunta (até 500 letras)", max_chars=500)
    if pergunta:
        if len(pergunta.strip()) < 2:
            ui.aviso("atencao", "Pergunta muito curta", "Escreva um pouco mais sobre o que precisa.")
        else:
            _perguntar_texto(pergunta.strip())
            st.rerun()
    if st.session_state.chat and st.button("🧹 Começar nova conversa"):
        st.session_state.chat = []
        st.rerun()


def _aba_voz() -> None:
    st.markdown("Aperte o microfone, fale sua pergunta e aperte de novo para terminar. Você vai **ouvir** a resposta.")
    st.caption("🔒 O áudio é usado só para entender a pergunta e é apagado logo depois. Nada é gravado.")
    audio = st.audio_input("Gravar pergunta", key="voz_pergunta")
    if audio is None:
        return
    dados = audio.getvalue()
    marca = hash(dados)
    if st.session_state.get("voz_marca") != marca:  # só processa um áudio novo, não a cada clique na tela
        st.session_state.voz_marca = marca
        try:
            with st.spinner("Ouvindo e procurando a resposta..."):
                r, ms = api.perguntar_por_voz("pergunta.wav", dados, "audio/wav")
            st.session_state.voz_resultado = r
            sessao.registrar("voz", "sem fonte" if r["abstencao"] else "respondida", ms)
        except api.ErroAPI as e:
            st.session_state.voz_resultado = {"erro": str(e)}
            sessao.registrar("voz", "erro", None)
    r = st.session_state.get("voz_resultado") or {}
    if "erro" in r:
        ui.aviso("erro", "Não consegui responder por voz", r["erro"])
        st.caption("Você pode escrever a pergunta na aba Escrever.")
        return
    st.markdown(f"**Você perguntou:** {r['transcricao'] or '(não entendi o áudio)'}")
    _mostrar_resposta({"resposta": r["resposta"], "fontes": r["fontes"], "abstencao": r["abstencao"]})
    if r["audio_base64"]:
        ui.tocar_audio(r["audio_base64"], r["formato_audio"])
    else:
        ui.aviso("atencao", "Não consegui gerar o áudio", "A resposta está escrita acima.")


def render() -> None:
    ui.cabecalho("Perguntar", "Respostas tiradas das páginas oficiais da prefeitura, sempre com a fonte. "
                              "Não substitui atendimento médico ou de emergência (192, 193, 190).")
    t_texto, t_voz = st.tabs(["✍️ Escrever", "🎤 Falar"])
    with t_texto:
        _aba_texto()
    with t_voz:
        _aba_voz()
