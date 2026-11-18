"""Identidade visual do EloBairro.

Ideia: a linguagem das placas de rua e da sinalização urbana. Azul-petróleo de placa como cor principal,
amarelo de faixa de pedestre só para o que exige atenção (alertas da casa, urgência), fundo frio e limpo.
Tipografia Atkinson Hyperlegible, desenhada pelo Braille Institute para quem tem baixa visão: as letras
parecidas (I, l, 1; O, 0; b, d) têm formas bem diferentes. É a escolha certa para o público do app.

Tokens
  tinta     #17283A  texto e títulos
  placa     #0E6A8A  ação principal, links, foco (contraste 5,9:1 sobre branco)
  placa-esc #0A5068  hover
  faixa     #F2B705  só para atenção (alerta da casa, urgência alta)
  fundo     #F3F6F9  fundo do app
  papel     #FFFFFF  superfícies
  linha     #D9E1E8  bordas
  calma     #2E7D4F  sucesso / "tudo certo"
  alerta    #B3261E  erro / urgência alta
Raios com hierarquia: blocos grandes 18 px, campos 10 px, etiquetas 999 px.
Movimento só quando responde a uma ação (protocolo aparece) ou pede atenção (aviso da casa),
e desligado para quem prefere menos movimento (prefers-reduced-motion).
"""
import streamlit as st

FONTE = "https://fonts.googleapis.com/css2?family=Atkinson+Hyperlegible:ital,wght@0,400;0,700;1,400&display=swap"

BASE = """
@import url('%(fonte)s');
:root {
  --tinta:#17283A; --tinta-2:#4A5B6C; --placa:#0E6A8A; --placa-esc:#0A5068; --placa-claro:#E3F1F6;
  --faixa:#F2B705; --faixa-claro:#FFF6D6; --fundo:#F3F6F9; --papel:#FFFFFF; --linha:#D9E1E8;
  --calma:#2E7D4F; --calma-claro:#E5F3EA; --alerta:#B3261E; --alerta-claro:#FBE9E7;
  --r-grande:18px; --r-campo:10px; --sombra:0 1px 2px rgba(23,40,58,.06), 0 6px 18px rgba(23,40,58,.06);
}
html, body, .stApp, .stApp p, .stApp li, .stApp label, .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp a,
button, input, textarea, select, .elb-cab, [data-testid="stMarkdownContainer"] {
  font-family:'Atkinson Hyperlegible', system-ui, -apple-system, 'Segoe UI', sans-serif !important;
}
[data-testid="stIconMaterial"], .material-symbols-rounded, [class*="material-symbols"] {
  font-family:'Material Symbols Rounded' !important; }
.stApp { background:var(--fundo); color:var(--tinta); }
[data-testid="stHeader"] { background:transparent; }
.block-container { padding-top:5rem !important; max-width:1180px; }
h1, h2, h3, h4 { color:var(--tinta); letter-spacing:-0.01em; font-weight:700 !important; }
p, li { line-height:1.55; }
a { color:var(--placa); text-underline-offset:3px; }
*:focus-visible { outline:3px solid var(--faixa) !important; outline-offset:2px !important; border-radius:6px; }

/* barra lateral */
[data-testid="stSidebar"] { background:var(--papel); border-right:1px solid var(--linha); }
[data-testid="stSidebar"] h3 { font-size:.95rem; color:var(--tinta-2); margin:1.2rem 0 .3rem; }

/* navegação do topo: pílulas */
[data-testid="stTopNavLink"], [data-testid="stNavLink"] { border-radius:999px !important; padding:.35rem .9rem !important; }
[data-testid="stTopNavLink"]:hover { background:var(--placa-claro) !important; }

/* botões e campos */
.stButton > button, .stDownloadButton > button, .stFormSubmitButton > button, [data-testid="stPageLink"] a {
  min-height:46px; border-radius:var(--r-campo); font-weight:700; transition:background .15s, box-shadow .15s, transform .08s;
}
.stButton > button:active, .stFormSubmitButton > button:active { transform:translateY(1px); }
[data-testid="stBaseButton-primary"], [data-testid="stBaseButton-primaryFormSubmit"] {
  background:var(--placa) !important; border-color:var(--placa) !important; color:#fff !important;
}
[data-testid="stBaseButton-primary"]:hover, [data-testid="stBaseButton-primaryFormSubmit"]:hover {
  background:var(--placa-esc) !important; box-shadow:0 4px 12px rgba(14,106,138,.28);
}
input, textarea, [data-baseweb="select"] > div { border-radius:var(--r-campo) !important; }
[data-testid="stWidgetLabel"] p { font-weight:700; color:var(--tinta); }

/* blocos com borda viram superfícies de papel */
[data-testid="stVerticalBlockBorderWrapper"]:has(> div > [data-testid="stVerticalBlock"]),
[data-testid="stForm"] {
  background:var(--papel); border:1px solid var(--linha) !important; border-radius:var(--r-grande) !important;
  box-shadow:var(--sombra);
}
[data-testid="stExpander"] details { background:var(--papel); border-radius:var(--r-campo); border-color:var(--linha); }
[data-testid="stAlertContainer"] { border-radius:var(--r-campo); }
[data-testid="stMetric"] { background:var(--papel); border:1px solid var(--linha); border-radius:var(--r-grande);
  padding:1rem 1.1rem; box-shadow:var(--sombra); }
[data-testid="stMetricValue"] { font-size:2.1rem; font-variant-numeric:tabular-nums; }
[data-testid="stChatMessage"] { background:var(--papel); border:1px solid var(--linha); border-radius:var(--r-grande); }
[data-testid="stTabs"] [role="tab"] { font-weight:700; }
[data-testid="stPlotlyChart"] { background:var(--papel); border:1px solid var(--linha); border-radius:var(--r-grande);
  padding:.4rem; box-shadow:var(--sombra); }

/* ---- componentes próprios (prefixo elb-) ---- */
.elb-cab { display:flex; align-items:flex-end; justify-content:space-between; gap:1rem; margin:0 0 1.2rem; }
.elb-cab h1 { font-size:2rem; margin:0; padding:0; line-height:1.15; }
.elb-cab p { margin:.35rem 0 0; color:var(--tinta-2); font-size:1.05rem; max-width:62ch; }
.elb-marca { display:flex; align-items:center; gap:.6rem; margin-bottom:.4rem; }
.elb-marca b { font-size:1.35rem; letter-spacing:-.01em; }
.elb-placa { display:inline-grid; place-items:center; width:40px; height:40px; border-radius:10px;
  background:var(--placa); color:#fff; font-weight:700; font-size:1.1rem; box-shadow:inset 0 0 0 3px #fff, 0 0 0 2px var(--placa); }

/* atalhos da página inicial (containers com key) */
[class*="st-key-atalho_"] { background:var(--papel) !important; border:1px solid var(--linha) !important;
  border-radius:var(--r-grande) !important; box-shadow:var(--sombra); padding:1.2rem 1.4rem !important;
  transition:border-color .15s, box-shadow .15s, transform .15s; }
[class*="st-key-atalho_"]:hover { border-color:var(--placa) !important; box-shadow:0 8px 24px rgba(14,106,138,.14) !important;
  transform:translateY(-2px); }
[class*="st-key-atalho_"] .ico { font-size:2.2rem; line-height:1; }
[class*="st-key-atalho_"] h3 { margin:.5rem 0 .1rem !important; padding:0 !important; font-size:1.3rem !important; }
[class*="st-key-atalho_"] p { color:var(--tinta-2); }
[class*="st-key-atalho_"] [data-testid="stPageLink"] a { background:var(--placa-claro); border-radius:999px; width:fit-content;
  padding:.35rem 1rem .35rem .8rem; }
[class*="st-key-atalho_"] [data-testid="stPageLink"] a p { color:var(--placa-esc) !important; font-weight:700; }
.st-key-atalho_relatar { background:var(--placa) !important; border-color:var(--placa) !important; min-height:370px;
  justify-content:center; padding:1.4rem 1.4rem !important; }
.st-key-atalho_relatar h3, .st-key-atalho_relatar p { color:#fff !important; }
.st-key-atalho_relatar h3 { font-size:1.75rem !important; }
.st-key-atalho_relatar [data-testid="stPageLink"] a { background:#fff; margin-top:.8rem; }
.st-key-atalho_relatar [data-testid="stPageLink"] a p { color:var(--placa) !important; }

/* passos do relato (é uma sequência de verdade) */
.elb-passos { display:flex; gap:.5rem; margin:.2rem 0 1.2rem !important; padding:0 !important; list-style:none; flex-wrap:wrap; }
.elb-passos li { display:flex; align-items:center; gap:.5rem; padding:.45rem .9rem .45rem .45rem; border-radius:999px;
  background:var(--papel); border:1px solid var(--linha); color:var(--tinta-2); font-weight:700; }
.elb-passos li span { display:inline-grid; place-items:center; width:28px; height:28px; border-radius:50%%;
  background:var(--fundo); color:var(--tinta-2); }
.elb-passos li.feito span { background:var(--calma); color:#fff; }
.elb-passos li.atual { border-color:var(--placa); color:var(--tinta); box-shadow:0 0 0 3px var(--placa-claro); }
.elb-passos li.atual span { background:var(--placa); color:#fff; }

/* etiquetas */
.elb-etq { display:inline-flex; align-items:center; gap:.35rem; padding:.2rem .7rem; border-radius:999px;
  font-weight:700; font-size:.92rem; border:1px solid transparent; white-space:nowrap; }
.elb-etq.alta { background:var(--alerta-claro); color:var(--alerta); border-color:#F2C4BF; }
.elb-etq.media { background:var(--faixa-claro); color:#7A5A00; border-color:#F3DE97; }
.elb-etq.baixa { background:var(--calma-claro); color:var(--calma); border-color:#BFE0CB; }
.elb-etq.neutra { background:var(--placa-claro); color:var(--placa-esc); border-color:#BCDDE8; }

/* proposta da IA */
.elb-proposta { background:var(--papel); border:1px solid var(--linha); border-left:6px solid var(--placa);
  border-radius:var(--r-campo); padding:1.1rem 1.2rem; margin:.2rem 0 1rem; box-shadow:var(--sombra); }
.elb-proposta .resumo { font-size:1.15rem; margin:0 0 .8rem; }
.elb-proposta .linha { display:flex; flex-wrap:wrap; gap:.5rem; }
.elb-proposta ul { margin:.8rem 0 0 !important; padding-left:1.1rem !important; color:var(--tinta-2); }

/* o elemento memorável: o protocolo como senha de atendimento */
.elb-senha { position:relative; display:grid; grid-template-columns:1fr auto; gap:1rem 1.6rem; align-items:center;
  background:var(--papel); border:2px solid var(--placa); border-radius:var(--r-grande); padding:1.4rem 1.6rem;
  box-shadow:0 10px 30px rgba(14,106,138,.16); margin:.4rem 0 1.4rem; animation:elb-entra .45s cubic-bezier(.2,.8,.2,1) both; }
.elb-senha::before, .elb-senha::after { content:""; position:absolute; top:50%%; width:22px; height:22px; border-radius:50%%;
  background:var(--fundo); border:2px solid var(--placa); transform:translateY(-50%%); }
.elb-senha::before { left:-12px; clip-path:inset(0 0 0 50%%); }
.elb-senha::after { right:-12px; clip-path:inset(0 50%% 0 0); }
.elb-senha .rot { color:var(--tinta-2); font-weight:700; margin:0; }
.elb-senha .num { font-size:2.3rem; font-weight:700; letter-spacing:0; color:var(--placa-esc); margin:.1rem 0 .6rem;
  font-variant-numeric:tabular-nums; word-break:break-all; }
.elb-senha dl { display:grid; grid-template-columns:max-content 1fr; gap:.35rem 1rem; margin:0 !important; padding:0 !important; }
.elb-senha dt { color:var(--tinta-2); }
.elb-senha dd { margin:0; font-weight:700; }
.elb-senha .prox { grid-column:1 / -1; margin:0; padding-top:.9rem; border-top:2px dashed var(--linha); }
.elb-senha .selo { display:grid; place-items:center; width:92px; height:92px; border-radius:50%%; background:var(--calma-claro);
  color:var(--calma); font-size:2.6rem; animation:elb-selo .5s .25s cubic-bezier(.3,1.6,.5,1) both; }
@media (max-width:640px){ .elb-senha{ grid-template-columns:1fr; } .elb-senha .selo{ display:none; } }

/* aviso da casa: amarelo de sinalização e um pulso que chama o olhar */
.elb-aviso { display:flex; align-items:center; gap:1.4rem; background:var(--faixa-claro); border:2px solid var(--faixa);
  border-radius:var(--r-grande); padding:1.4rem 1.6rem; margin:.4rem 0 1rem; }
.elb-aviso .anel { position:relative; flex:none; display:grid; place-items:center; width:84px; height:84px; border-radius:50%%;
  background:var(--faixa); font-size:2.4rem; }
.elb-aviso .anel::after { content:""; position:absolute; inset:0; border-radius:50%%; border:4px solid var(--faixa);
  animation:elb-pulso 1.6s ease-out infinite; }
.elb-aviso .txt { font-size:2rem; font-weight:700; line-height:1.15; margin:0; }
.elb-aviso .meta { margin:.35rem 0 0; color:#5C4700; font-size:1.05rem; }
.elb-aviso.antigo { background:var(--papel); border-color:var(--linha); }
.elb-aviso.antigo .anel { background:var(--fundo); }
.elb-aviso.antigo .anel::after { display:none; }
.elb-aviso.antigo .meta { color:var(--tinta-2); }

.elb-lista { list-style:none; margin:0 !important; padding:0 !important; }
.elb-lista li { display:flex; justify-content:space-between; gap:1rem; padding:.6rem 0; border-bottom:1px solid var(--linha); }
.elb-lista li:last-child { border-bottom:0; }
.elb-lista .q { color:var(--tinta-2); }

.elb-vazio { text-align:center; background:var(--papel); border:2px dashed var(--linha); border-radius:var(--r-grande);
  padding:2rem 1.2rem; color:var(--tinta-2); }
.elb-vazio .ico { font-size:2.4rem; }
.elb-vazio b { display:block; color:var(--tinta); font-size:1.15rem; margin:.4rem 0 .2rem; }

.elb-status { display:flex; align-items:center; gap:.5rem; font-weight:700; }
.elb-status i { width:10px; height:10px; border-radius:50%%; background:var(--calma); box-shadow:0 0 0 4px var(--calma-claro); }
.elb-status.fora i { background:var(--alerta); box-shadow:0 0 0 4px var(--alerta-claro); }

@keyframes elb-entra { from { opacity:0; transform:translateY(10px) scale(.98); } to { opacity:1; transform:none; } }
@keyframes elb-selo { from { opacity:0; transform:scale(.4) rotate(-20deg); } to { opacity:1; transform:none; } }
@keyframes elb-pulso { from { transform:scale(1); opacity:.9; } to { transform:scale(1.55); opacity:0; } }
@media (prefers-reduced-motion: reduce) { *, *::before, *::after { animation:none !important; transition:none !important; } }
"""

LETRA_GRANDE = "html { font-size:20px !important; } .elb-aviso .txt{ font-size:2.4rem; }"

ALTO_CONTRASTE = """
:root { --tinta:#FFFFFF; --tinta-2:#FFFFFF; --fundo:#000000; --papel:#000000; --linha:#FFFFFF;
  --placa:#FFD60A; --placa-esc:#FFD60A; --placa-claro:#222; --faixa-claro:#000; --calma-claro:#000; --alerta-claro:#000; }
.stApp, [data-testid="stSidebar"], [data-testid="stSidebarContent"], [data-testid="stHeader"],
[data-testid="stBottomBlockContainer"] { background:#000 !important; }
.stApp *:not(svg *) { color:#fff !important; }
input, textarea, [data-baseweb="select"] > div, [data-testid="stChatInput"] { background:#000 !important; border:2px solid #fff !important; }
.stApp button[kind^="primary"] { background:#FFD60A !important; border:2px solid #FFD60A !important; }
.stApp button[kind^="primary"], .stApp button[kind^="primary"] * { color:#000 !important; }
.stButton button[kind^="secondary"], .stFormSubmitButton button[kind^="secondary"], .stDownloadButton button,
[data-testid="stFileUploaderDropzone"] button { border:2px solid #FFD60A !important; background:#000 !important; }
[data-testid="stFileUploaderDropzone"] { background:#000 !important; border:2px dashed #fff !important; }
[data-testid="stButtonGroup"] button { background:#000 !important; border:2px solid #FFD60A !important; }
[data-testid="stButtonGroup"] button[aria-checked="true"], [data-testid="stButtonGroup"] button[kind*="Active"] {
  background:#FFD60A !important; }
[data-testid="stButtonGroup"] button[aria-checked="true"] *, [data-testid="stButtonGroup"] button[kind*="Active"] * {
  color:#000 !important; }
[data-baseweb="select"] * { background-color:#000 !important; }
.elb-passos li.atual span, .elb-passos li.feito span { color:#000 !important; background:#FFD60A !important; }
a, a * { color:#FFD60A !important; text-decoration:underline; }
.elb-atalho.principal, .elb-atalho.principal * { background:#FFD60A !important; color:#000 !important; }
.elb-aviso { border-color:#FFD60A; } .elb-aviso .anel { background:#FFD60A; }
.elb-etq { border-color:#fff !important; }
[data-testid="stCaptionContainer"] { opacity:1 !important; }
::placeholder { color:#ccc !important; }
"""


def aplicar(letra_grande: bool, alto_contraste: bool) -> None:
    css = BASE % {"fonte": FONTE}
    if letra_grande:
        css += LETRA_GRANDE
    if alto_contraste:
        css += ALTO_CONTRASTE
    st.html(f"<style>{css}</style>")
