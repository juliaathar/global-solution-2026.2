"""Interface Gradio do assistente de voz EloBairro.

    python app.py            # modelos reais (veja .env)
    python app.py --demo     # módulos falsos, só para testar a interface
"""
import argparse

import gradio as gr

from componentes import carregar_componentes
from config import LLM_PROVIDER, SAIDA_DIR, STT_MODEL, TTS_ENGINE, USA_NUVEM
from llm import Assistente
from pipeline import PipelineVoz

ETAPAS = ["stt", "llm_rag", "adaptacao", "tts", "total"]
CABECALHO_TABELA = ["Turno", "STT (s)", "LLM+RAG (s)", "Adaptação (s)", "TTS (s)", "Total (s)"]


# ---------------------------------------------------------------- consentimento
def texto_consentimento(demo: bool) -> str:
    if demo:
        return ("### Modo demonstração\nNenhum modelo real está sendo usado: a transcrição, a resposta "
                "e a voz são simuladas, e nada sai deste computador.")
    partes = [
        "### Antes de começar\n",
        "- Sua **voz será gravada e processada** para responder à sua pergunta.",
        f"- A transcrição é feita **neste computador** (faster-whisper `{STT_MODEL}`). "
        "O áudio é **apagado logo depois** de virar texto.",
        "- A voz que responde é **sintética**, não é a voz de nenhuma pessoa real.",
    ]
    if USA_NUVEM:
        enviados = []
        if LLM_PROVIDER != "ollama":
            enviados.append(f"o **texto da sua pergunta** é enviado ao serviço de IA `{LLM_PROVIDER}`")
        if TTS_ENGINE == "edge-tts":
            enviados.append("o **texto da resposta** é enviado ao serviço de voz `edge-tts` (Microsoft)")
        partes.append("- **Internet:** " + " e ".join(enviados) + ". Seu áudio não é enviado. "
                      "Não diga nome completo, CPF, endereço ou dados de saúde.")
    partes.append("- Este assistente **não substitui** médico, advogado ou atendimento de emergência. "
                  "Em emergência, ligue 192, 193 ou 190.")
    return "\n".join(partes)


# ---------------------------------------------------------------- interface
def construir(demo: bool) -> gr.Blocks:
    stt, llm, base, tts = carregar_componentes(demo)
    SAIDA_DIR.mkdir(exist_ok=True)
    log = SAIDA_DIR / "latencia.csv"

    def novo_pipeline() -> PipelineVoz:  # uma conversa (memória) por sessão do navegador
        return PipelineVoz(stt, Assistente(llm, base), tts, log)

    def aceitar(concordo):
        if not concordo:
            gr.Warning("Marque a caixa para concordar antes de continuar.")
            return gr.update(), gr.update()
        return gr.update(visible=False), gr.update(visible=True)

    def falar(audio, chat, tabela, pipeline):
        if not audio:
            gr.Warning("Grave ou envie um áudio primeiro.")
            return chat, tabela, None, pipeline, None
        pipeline = pipeline or novo_pipeline()
        r = pipeline.turno(audio)
        chat = chat + [{"role": "user", "content": r.transcricao or "(não entendi o áudio)"},
                       {"role": "assistant", "content": r.resposta_texto}]
        linhas = tabela.values.tolist() if hasattr(tabela, "values") else list(tabela or [])  # Gradio envia DataFrame
        tabela = linhas + [[len(linhas) + 1] + [round(r.latencias[e], 2) for e in ETAPAS]]
        return chat, tabela, r.audio_saida, pipeline, None

    def reiniciar():
        return [], [], None, None, None

    with gr.Blocks(title="EloBairro: assistente de voz") as app:
        gr.Markdown("# EloBairro: assistente de voz\nPergunte por voz sobre serviços públicos do bairro.")
        pipeline_estado = gr.State(None)

        with gr.Column(visible=True) as tela_consentimento:
            gr.Markdown(texto_consentimento(demo))
            concordo = gr.Checkbox(label="Li o aviso e concordo em usar o assistente")
            comecar = gr.Button("Começar", variant="primary")

        with gr.Column(visible=False) as tela_principal:
            audio_in = gr.Audio(sources=["microphone", "upload"], type="filepath",
                                label="Aperte para gravar (ou envie um arquivo de áudio) e depois toque em Enviar")
            enviar = gr.Button("Enviar pergunta", variant="primary")
            chat = gr.Chatbot(type="messages", label="Conversa (texto)", height=320)
            audio_out = gr.Audio(label="Resposta falada", autoplay=True, type="filepath",
                                 interactive=False)
            tabela = gr.Dataframe(headers=CABECALHO_TABELA, label="Latência por etapa (segundos)",
                                  interactive=False, value=[])
            nova = gr.Button("Nova conversa")

        comecar.click(aceitar, concordo, [tela_consentimento, tela_principal])
        enviar.click(falar, [audio_in, chat, tabela, pipeline_estado],
                     [chat, tabela, audio_out, pipeline_estado, audio_in])
        nova.click(reiniciar, None, [chat, tabela, audio_out, pipeline_estado, audio_in])
    return app


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--demo", action="store_true", help="usa módulos falsos (sem modelos)")
    ap.add_argument("--porta", type=int, default=7860)
    args = ap.parse_args()
    construir(args.demo).launch(server_name="127.0.0.1", server_port=args.porta,
                                allowed_paths=[str(SAIDA_DIR)], show_error=True)
