"""Relatar problema do bairro: texto + foto opcional -> proposta da IA -> cidadão confere -> protocolo.

Human-in-the-loop: a IA só propõe. O protocolo só é criado quando o cidadão marca que conferiu e
aperta "Confirmar". Ele pode corrigir assunto e urgência antes.
"""
import streamlit as st

from web.providers import api_cliente as api
from web.providers import api_visao
from html import escape

from web.state import sessao
from web.ui import componentes as ui

REGIOES = ["Não informada", "Centro", "Norte", "Sul", "Leste", "Oeste", "Sudeste"]
CATEGORIAS = {"buraco": "Buraco na rua", "iluminacao": "Iluminação pública", "lixo": "Lixo e entulho",
              "calcada": "Calçada danificada", "alagamento": "Alagamento ou bueiro",
              "servico_saude": "Serviço de saúde", "indefinido": "Outro assunto"}
URGENCIAS = {"alta": "🔴 Alta: risco a pessoas", "media": "🟠 Média", "baixa": "🟢 Baixa"}
TEXTO_MIN, TEXTO_MAX = 10, 500
FOTO_MAX_MB = 5


def validar(texto: str, foto) -> list[str]:
    """Validação no front (a API valida de novo): obrigatório, tamanho e formato."""
    erros = []
    t = " ".join((texto or "").split())
    if not t:
        erros.append("Conte o que aconteceu. Esse campo é obrigatório.")
    elif len(t) < TEXTO_MIN:
        erros.append(f"Escreva pelo menos {TEXTO_MIN} letras.")
    elif len(t) > TEXTO_MAX:
        erros.append(f"O texto passou de {TEXTO_MAX} letras. Resuma um pouco.")
    if foto is not None:
        if foto.type not in ("image/jpeg", "image/png"):
            erros.append("A foto precisa ser JPG ou PNG.")
        elif foto.size > FOTO_MAX_MB * 1024 * 1024:
            erros.append(f"A foto passou de {FOTO_MAX_MB} MB.")
    return erros


def _formulario() -> None:
    v = st.session_state.versao_form
    with st.form(f"relato_{v}"):
        texto = st.text_area("O que aconteceu e onde? (obrigatório)", max_chars=TEXTO_MAX, height=130,
                             placeholder="Ex.: Poste apagado na Rua das Flores, perto da escola. Está tudo escuro à noite.",
                             help="Diga o problema e um ponto de referência. Não precisa colocar seu nome ou telefone.")
        c1, c2 = st.columns(2)
        regiao = c1.selectbox("Região da cidade", REGIOES, help="Ajuda a equipe a organizar os pedidos.")
        foto = c2.file_uploader("Foto (opcional: JPG ou PNG, até 5 MB)", type=["jpg", "jpeg", "png"])
        enviado = st.form_submit_button("Analisar meu relato", type="primary", width="stretch")
    if not enviado:
        return
    erros = validar(texto, foto)
    if erros:
        for e in erros:
            ui.aviso("atencao", "Falta ajustar", e)
        return
    resultado_foto = None
    if foto is not None:
        try:
            with st.spinner("Olhando a foto..."):
                resultado_foto = api_visao.classificar_imagem(foto, 0.45)
            sessao.registrar("foto", "fissura" if resultado_foto["inspecao_recomendada"] else "sem fissura",
                             resultado_foto.get("latencia_ms"))
        except api_visao.ErroAPI as e:
            ui.aviso("atencao", "Não consegui analisar a foto", f"{e} Seguimos só com o texto.")
            sessao.registrar("foto", "erro", None)
    try:
        with st.spinner("Entendendo o seu relato..."):
            proposta, ms = api.analisar_relato(texto.strip(), regiao, "foto" if resultado_foto else "texto",
                                               resultado_foto)
    except api.ErroAPI as e:
        ui.erro_api(e, "Não consegui analisar o relato")
        sessao.registrar("relato", "erro", None)
        return
    sessao.registrar("relato", "proposta " + proposta["metodo"], ms, categoria=proposta["categoria"])
    st.session_state.proposta = proposta
    st.session_state.foto_resultado = resultado_foto
    st.rerun()  # mostra a proposta para o cidadão conferir


def _proposta() -> None:
    p = st.session_state.proposta
    metodo = "assistente de IA" if p["metodo"] == "llm" else "classificação automática"
    certeza = "alta" if p["confianca"] >= 0.85 else "média" if p["confianca"] >= 0.7 else "baixa"
    avisos = "".join(f"<li>{escape(a)}</li>" for a in p["avisos"])
    ui._html(f"""<div class='elb-proposta'>
  <p class='resumo'>“{escape(p['resumo'])}”</p>
  <div class='linha'>{ui.etiqueta(p['categoria_rotulo'])}{ui.etiqueta_urg_html(p['urgencia'])}
    {ui.etiqueta('Região: ' + p['regiao'])}{ui.etiqueta(f"Certeza {certeza} ({p['confianca']:.0%})")}</div>
  {f"<ul>{avisos}</ul>" if avisos else ""}
  <p style='margin:.8rem 0 0;color:var(--tinta-2);font-size:.95rem'>Entendido por {metodo}. Confira e corrija se precisar.</p>
</div>""")
    if st.session_state.foto_resultado:
        f = st.session_state.foto_resultado
        st.caption(("⚠️ Possível fissura na foto" if f["inspecao_recomendada"] else "✅ Sem fissura visível na foto")
                   + f" (probabilidade {f['probabilidade_fissura']:.0%}). Triagem apenas.")
    if p["duplicado_de"]:
        ui.aviso("info", f"Já existe o protocolo {p['duplicado_de']} para um problema muito parecido",
                 "Se confirmar, seu aviso será juntado a ele em vez de abrir outro.")
    if p["precisa_revisao"]:
        ui.aviso("atencao", "Não temos certeza do assunto", "Escolha abaixo o assunto certo antes de confirmar.")

    st.markdown("**Está certo? Se não, corrija aqui:**")
    c1, c2 = st.columns(2)
    cats = list(CATEGORIAS)
    cat = c1.selectbox("Assunto", cats, index=cats.index(p["categoria"]), format_func=CATEGORIAS.get)
    urgs = list(URGENCIAS)
    urg = c2.radio("Prioridade", urgs, index=urgs.index(p["urgencia"]), format_func=URGENCIAS.get, horizontal=True)
    conferi = st.checkbox("Conferi as informações e quero registrar o pedido")
    b1, b2 = st.columns(2)
    if b1.button("✅ Confirmar e gerar protocolo", type="primary", disabled=not conferi, width="stretch"):
        corrigiu = cat != p["categoria"] or urg != p["urgencia"]
        corpo = {"confirmado": True, "texto_mascarado": p["texto_mascarado"], "categoria": cat, "urgencia": urg,
                 "confianca": 1.0 if corrigiu else p["confianca"], "metodo": p["metodo"], "regiao": p["regiao"],
                 "origem": p["origem"], "corrigido_pelo_cidadao": corrigiu,
                 "probabilidade_fissura": (st.session_state.foto_resultado or {}).get("probabilidade_fissura")}
        try:
            with st.spinner("Registrando..."):
                prot, ms = api.confirmar_relato(corpo)
        except api.ErroAPI as e:
            ui.erro_api(e, "Não consegui registrar. Seu relato não foi perdido: tente de novo.")
            return
        sessao.registrar("protocolo", "novo" if prot["novo"] else "juntado", ms, categoria=cat,
                         corrigido=corrigiu)
        st.session_state.meus_protocolos.insert(0, prot)
        st.session_state.mostrar_protocolo = True
        sessao.limpar_relato()
        st.rerun()
    if b2.button("✏️ Voltar e mudar o texto", width="stretch"):
        sessao.registrar("relato", "descartado pelo cidadão", None)
        sessao.limpar_relato()
        st.rerun()


def _protocolo() -> None:
    ultimo = st.session_state.meus_protocolos[0]
    if ultimo["novo"]:
        st.toast("Pedido registrado", icon="✅")
    else:
        ui.aviso("info", "Esse problema já estava registrado", "Seu aviso foi juntado ao protocolo abaixo.")
    ui.cartao_protocolo(ultimo)
    c1, c2 = st.columns([1, 2])
    if c1.button("Relatar outro problema", type="primary", width="stretch"):
        st.session_state.mostrar_protocolo = False
        st.rerun()
    if len(st.session_state.meus_protocolos) > 1:
        with st.expander(f"Outros protocolos desta visita ({len(st.session_state.meus_protocolos) - 1})"):
            for p in st.session_state.meus_protocolos[1:]:
                st.markdown(f"- **{p['protocolo']}**: {p['categoria_rotulo']} ({ui.etiqueta_urgencia(p['urgencia'])})")


def render() -> None:
    ui.cabecalho("Relatar um problema",
                 "Conte o que aconteceu e onde. Você confere antes de enviar e recebe um número de protocolo.")
    if st.session_state.get("mostrar_protocolo") and st.session_state.meus_protocolos:
        ui.passos(4)
        _protocolo()
    elif st.session_state.proposta:
        ui.passos(2)
        _proposta()
    else:
        ui.passos(1)
        _formulario()
        st.caption("🔒 Telefone, CPF, e-mail e nome são tirados do texto antes de qualquer análise.")
