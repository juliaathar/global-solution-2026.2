# Roteiro do vídeo de Front-end (até 5 min)

O enunciado pede: problema, fluxo, código, erro tratado e evidências. Grave a tela em 1080p e fale com calma.
Antes de gravar: `docker compose up` (ou API + Streamlit), abrir http://localhost:8501 e, no painel do gestor,
clicar em "Importar do robô RPA" para ter dados.

| Tempo | O que mostrar | O que falar (resumo) |
|---|---|---|
| 0:00–0:30 | Tela inicial | Problema: idosos, pessoas com baixa alfabetização e com deficiência têm dificuldade com canais de texto. ODS 10 e 16. |
| 0:30–1:00 | Barra lateral: letra grande, alto contraste, ouvir respostas | Cuidados de acessibilidade. Cor sempre com ícone e texto. |
| 1:00–1:40 | Perguntar: pergunta escrita e a aba Falar | Resposta do RAG (03) com fonte oficial. Voz pela pasta 02. |
| 1:40–2:40 | Relatar problema: enviar vazio (erro de validação), depois texto com telefone + foto | Validação; telefone sumiu do texto (máscara do robô 06); a foto passou pela visão (04). A IA só propõe: o cidadão corrige e confirma. Protocolo com encaminhamento. |
| 2:40–3:20 | Gestor: filtros, gráficos Plotly, mapa, revisão humana | Painel junta protocolos do app e do robô RPA; dois filtros combinados; mudar status. |
| 3:20–3:45 | Avisos da casa: simulador ou celular com o OuviAí (05) | Campainha vira alerta visual; ambiente não alerta. |
| 3:45–4:20 | **Erro tratado**: parar a API (Ctrl+C) e recarregar; ou `LLM_PROVIDER` com chave errada | "Sistema fora do ar" sem travar a tela; LLM fora do ar cai para as regras e avisa. |
| 4:20–4:50 | Código: `api/main.py`, `pipelines/relato_pipeline.py`, `web/features/relatar.py` | Separação front/back; LLM só no back-end; saída validada com Pydantic. |
| 4:50–5:00 | Terminal com `python -m pytest testes -v` e `evidencias/casos_teste_ia.md` | Evidências: 32 testes e os 3 casos da IA. |
