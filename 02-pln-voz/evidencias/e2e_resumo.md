# Ponta a ponta: resultados

Configuração: STT faster-whisper-base, LLM ollama/qwen2.5:1.5b, TTS piper.
10 conversas, 30 turnos.

| Etapa | Média (s) | Máximo (s) |
|---|---|---|
| stt | 1.48 | 1.76 |
| llm_rag | 14.58 | 86.44 |
| adaptacao | 0.00 | 0.00 |
| tts | 1.70 | 7.65 |
| total | 17.76 | 95.86 |

`total` é o tempo da pergunta até a resposta estar pronta para tocar, isto é, o início da fala.

## Como as respostas foram geradas

| Origem | Turnos |
|---|---|
| llm | 14 |
| sem_contexto | 16 |