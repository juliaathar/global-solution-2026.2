"""Gera relatorio/figuras/arquitetura.png (diagrama do fluxo de um turno do assistente de voz).

Uso: pip install matplotlib && python relatorio/gerar_diagrama.py
"""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyBboxPatch  # noqa: E402

SAIDA = Path(__file__).resolve().parent / "figuras" / "arquitetura.png"
AZUL, VERDE, LARANJA, CINZA = "#dbe7f7", "#dcefdc", "#fde6c8", "#eeeeee"
BORDA = "#34495e"
W, H = 2.45, 0.95


def caixa(ax, x, y, titulo, detalhe="", cor=AZUL, w=W, h=H, tracejada=False):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.08", fc=cor, ec=BORDA,
                                lw=1.4, ls="--" if tracejada else "-"))
    ax.text(x + w / 2, y + h * (0.64 if detalhe else 0.5), titulo, ha="center", va="center", fontsize=10,
            fontweight="bold", color="#1b2733")
    if detalhe:
        ax.text(x + w / 2, y + h * 0.28, detalhe, ha="center", va="center", fontsize=8, color="#34495e")


def seta(ax, p, q, rotulo="", tracejada=False, cor=BORDA, deslocamento=(0, 0.12)):
    ax.annotate("", xy=q, xytext=p, arrowprops=dict(arrowstyle="-|>", color=cor, lw=1.5,
                                                    ls="--" if tracejada else "-", shrinkA=0, shrinkB=0))
    if rotulo:
        ax.text((p[0] + q[0]) / 2 + deslocamento[0], (p[1] + q[1]) / 2 + deslocamento[1], rotulo, ha="center",
                va="bottom", fontsize=8, color=cor, style="italic")


def main():
    fig, ax = plt.subplots(figsize=(11, 6.2))
    ax.set_xlim(0, 11)
    ax.set_ylim(-0.05, 6.2)
    ax.axis("off")
    xs = [0.05, 2.85, 5.65, 8.45]
    y1, y2 = 4.15, 1.75

    # linha 1
    caixa(ax, xs[0], y1, "Captura de áudio", "microfone ou upload\n(aviso de consentimento)")
    caixa(ax, xs[1], y1, "STT", "faster-whisper\n(local, base ou small)")
    caixa(ax, xs[2], y1, "Guardas", "emergência, silêncio,\ncontinuação da conversa", LARANJA)
    caixa(ax, xs[3], y1, "Base de conhecimento", "RAG da pasta 03\ncorpus de SJC, e5-large, top-3", VERDE)
    for i in range(3):
        seta(ax, (xs[i] + W, y1 + H / 2), (xs[i + 1], y1 + H / 2))

    # desvios com resposta fixa (não passam pelo LLM)
    caixa(ax, xs[2], 5.35, "Resposta fixa", "192, 193 e 190", CINZA, h=0.7, tracejada=True)
    seta(ax, (xs[2] + W / 2, y1 + H), (xs[2] + W / 2, 5.35), "emergência", deslocamento=(0.62, -0.1))
    caixa(ax, xs[3], 5.35, "Resposta fixa", "\"não sei\" (sem evidência)", CINZA, h=0.7, tracejada=True)
    seta(ax, (xs[3] + W / 2, y1 + H), (xs[3] + W / 2, 5.35), "sem contexto", deslocamento=(0.66, -0.1))

    # da linha 1 para a linha 2
    ax.plot([xs[3] + W / 2, xs[3] + W / 2], [y1, 3.45], color=BORDA, lw=1.5)
    ax.plot([xs[3] + W / 2, xs[0] + W / 2], [3.45, 3.45], color=BORDA, lw=1.5)
    seta(ax, (xs[0] + W / 2, 3.45), (xs[0] + W / 2, y2 + H))
    ax.text(5.6, 3.5, "trechos recuperados", ha="center", va="bottom", fontsize=8, style="italic", color=BORDA)

    # linha 2
    caixa(ax, xs[0], y2, "LLM", "system prompt + memória\nOllama, OpenAI, Groq, Gemini")
    caixa(ax, xs[1], y2, "Adaptação para fala", "sem markdown nem emoji;\nnúmeros e siglas por extenso", LARANJA)
    caixa(ax, xs[2], y2, "TTS", "Piper (local)\nou edge-tts (nuvem)")
    caixa(ax, xs[3], y2, "Alto-falante", "texto da resposta\ntambém na tela", AZUL)
    for i in range(3):
        seta(ax, (xs[i] + W, y2 + H / 2), (xs[i + 1], y2 + H / 2))

    # respostas fixas também passam pela adaptação e pelo TTS
    ax.text(0.05, 5.75, "As respostas fixas (tracejadas) também\npassam pela adaptação para fala e pelo TTS.", ha="left",
            va="center", fontsize=8.5, color="#555555", style="italic")

    # latência
    caixa(ax, 3.9, 0.05, "Registro de latência", "tempo de cada etapa e total (latencia.csv)", CINZA, w=3.4, h=0.7,
          tracejada=True)
    for x in (xs[1] + W / 2, xs[2] + W / 2):
        seta(ax, (x, y2), (3.9 + 1.7 + (x - 5.6) * 0.4, 0.75), tracejada=True, cor="#7f8c8d")
    ax.set_title("Fluxo de um turno do assistente de voz do EloBairro", fontsize=13, fontweight="bold", pad=4)
    SAIDA.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(SAIDA, dpi=170, bbox_inches="tight", facecolor="white")
    print("Gerado:", SAIDA)


if __name__ == "__main__":
    main()
