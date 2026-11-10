# 02 PLN: Assistente de Voz

Entrega: um link (repositório) + relatório em PDF + vídeo de até 5 min.

## Checklist
- [ ] Captura por microfone e upload de áudio
- [ ] STT em português (módulo separado)
- [ ] LLM com system prompt (papel, tom, limites)
- [ ] Memória da conversa (perguntas de continuação)
- [ ] Base de conhecimento (RAG, reutilizando src/rag)
- [ ] Adaptação para fala (frases curtas, sem markdown e emoji, números e siglas legíveis)
- [ ] TTS em português do Brasil
- [ ] Interface mostra transcrição e resposta em texto
- [ ] Latência por etapa e total
- [ ] LGPD: consentimento, retenção mínima, recusa fora do tema, sem voz clonada
- [ ] Testes: STT 20 áudios (WER, jiwer, 3 vozes, 5 com ruído); LLM 30 perguntas (5 de continuação, 5 fora do escopo); TTS 10 respostas com 3 avaliadores; ponta a ponta 10 conversas de 3+ turnos
- [ ] Comparar duas opções em um componente (ex.: Whisper base vs small)
- [ ] README com modelos, versão e licença; nomes completos
- [ ] Vídeo: conversa de 3+ turnos com continuação e recusa
