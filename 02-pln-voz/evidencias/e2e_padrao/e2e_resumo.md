# Ponta a ponta: resultados

Configuração: STT faster-whisper-small, LLM ollama/qwen2.5:3b, TTS edge-tts.
10 conversas, 30 turnos.

| Etapa | Média (s) | Máximo (s) |
|---|---|---|
| stt | 5.17 | 18.98 |
| llm_rag | 38.41 | 110.84 |
| adaptacao | 0.00 | 0.01 |
| tts | 1.50 | 9.94 |
| total | 45.08 | 123.20 |

`total` é o tempo da pergunta até a resposta estar pronta para tocar, isto é, o início da fala.

## Como as respostas foram geradas

| Origem | Turnos |
|---|---|
| llm | 20 |
| sem_contexto | 10 |