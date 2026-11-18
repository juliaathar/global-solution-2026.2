"""Componentes reutilizáveis da interface. Cor nunca é o único sinal: todo estado tem ícone e texto.

Os componentes em HTML (cabeçalho, passos, senha do protocolo, aviso da casa) usam as classes elb-* de
ui/tema.py. Todo texto vindo do usuário ou da API passa por html.escape antes de entrar no HTML.
"""
import base64
from html import escape

import streamlit as st

from web.ui import tema

# nível -> (ícone, rótulo lido pelo leitor de tela, função do Streamlit com a cor semântica)
NIVEIS = {
    "sucesso": ("✅", "Tudo certo", st.success),
    "info": ("ℹ️", "Informação", st.info),
    "atencao": ("⚠️", "Atenção", st.warning),
    "erro": ("⛔", "Problema", st.error),
}
URGENCIA = {"alta": ("🔴", "Urgência alta"), "media": ("🟠", "Urgência média"), "baixa": ("🟢", "Urgência baixa")}
STATUS = {"aberto": "📬 Aberto", "em_analise": "🔎 Em análise por uma pessoa", "resolvido": "✔️ Resolvido"}


def _html(conteudo: str) -> None:
    st.html(conteudo)


def cabecalho(titulo: str, texto: str = "") -> None:
    """Título da página com uma frase que diz para que ela serve."""
    _html(f"<div class='elb-cab'><div><h1>{escape(titulo)}</h1>"
          + (f"<p>{escape(texto)}</p>" if texto else "") + "</div></div>")


def passos(atual: int, nomes=("Contar o problema", "Conferir", "Protocolo")) -> None:
    """Indicador de etapas do relato. atual começa em 1."""
    itens = []
    for i, nome in enumerate(nomes, 1):
        classe = "feito" if i < atual else "atual" if i == atual else ""
        marca = "✓" if i < atual else str(i)
        rotulo = f"Etapa {i} de {len(nomes)}: {nome}" + (" (concluída)" if i < atual else " (agora)" if i == atual else "")
        itens.append(f"<li class='{classe}' aria-label='{escape(rotulo)}'><span>{marca}</span>{escape(nome)}</li>")
    _html(f"<ol class='elb-passos'>{''.join(itens)}</ol>")


def aviso(nivel: str, titulo: str, texto: str = "") -> None:
    """Caixa de status semântica: ícone + palavra do nível + título + texto."""
    icone, rotulo, funcao = NIVEIS[nivel]
    corpo = f"**{rotulo}: {titulo}**" + (f"\n\n{texto}" if texto else "")
    funcao(corpo, icon=icone)


def etiqueta_urgencia(urgencia: str) -> str:
    """Texto simples (para markdown, tabelas e selects)."""
    icone, texto = URGENCIA.get(urgencia, ("⚪", urgencia))
    return f"{icone} {texto}"


def etiqueta(texto: str, tipo: str = "neutra") -> str:
    """Etiqueta em HTML. tipo: alta, media, baixa ou neutra."""
    return f"<span class='elb-etq {tipo}'>{escape(texto)}</span>"


def etiqueta_urg_html(urgencia: str) -> str:
    icone, texto = URGENCIA.get(urgencia, ("⚪", urgencia))
    return etiqueta(f"{icone} {texto}", urgencia if urgencia in URGENCIA else "neutra")


def estado_vazio(texto: str, dica: str = "", icone: str = "📭") -> None:
    _html(f"<div class='elb-vazio' role='status'><div class='ico' aria-hidden='true'>{icone}</div>"
          f"<b>{escape(texto)}</b>{escape(dica)}</div>")


def erro_api(erro: Exception, acao: str = "") -> None:
    aviso("erro", acao or "Não deu certo", str(erro))


def cartao_protocolo(p: dict) -> None:
    """A senha de atendimento: número grande, assunto, prioridade, para onde foi e o próximo passo."""
    _html(f"""
<section class='elb-senha' role='status' aria-live='polite'>
  <div>
    <p class='rot'>Seu protocolo</p>
    <p class='num'>{escape(p['protocolo'])}</p>
    <dl>
      <dt>Assunto</dt><dd>{escape(p['categoria_rotulo'])}</dd>
      <dt>Prioridade</dt><dd>{etiqueta_urg_html(p['urgencia'])}</dd>
      <dt>Vai para</dt><dd>{escape(p['encaminhamento'])}</dd>
      <dt>Situação</dt><dd>{escape(STATUS.get(p['status'], p['status']))}</dd>
    </dl>
  </div>
  <div class='selo' aria-hidden='true'>✓</div>
  <p class='prox'>➡️ {escape(p['proximo_passo'])}</p>
</section>""")


def aviso_casa(icone: str, mensagem: str, detalhe: str, recente: bool) -> None:
    """Aviso grande da campainha ou batida. Pulsa só enquanto é recente (menos de 2 minutos)."""
    _html(f"<div class='elb-aviso {'' if recente else 'antigo'}' role='alert' aria-live='assertive'>"
          f"<div class='anel' aria-hidden='true'>{icone}</div>"
          f"<div><p class='txt'>{escape(mensagem)}</p><p class='meta'>{escape(detalhe)}</p></div></div>")


def status_sistema(no_ar: bool, texto: str) -> None:
    _html(f"<div class='elb-status {'' if no_ar else 'fora'}' role='status'><i aria-hidden='true'></i>{escape(texto)}</div>")


def tocar_audio(audio_base64: str, formato: str) -> None:
    if audio_base64:
        st.audio(base64.b64decode(audio_base64), format=f"audio/{'mpeg' if formato == 'mp3' else formato}")


def aplicar_estilo(letra_grande: bool, alto_contraste: bool) -> None:
    """Tema do app + ajustes de acessibilidade escolhidos na barra lateral."""
    tema.aplicar(letra_grande, alto_contraste)
