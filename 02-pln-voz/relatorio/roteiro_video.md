# Roteiro do vídeo: Assistente de Voz do EloBairro (PLN)

Duração máxima: 5 minutos. O enunciado exige uma conversa real por voz com pelo menos 3 turnos, incluindo uma pergunta de continuação e uma recusa. O critério "Relatório e vídeo" também avalia problema, persona, ODS, justificativas e a demonstração funcionando.

## Roteiro

| Tempo | O que mostrar | O que falar |
|---|---|---|
| 0:00–0:30 | Tela inicial do app e o diagrama da arquitetura | Nome do projeto e dos integrantes. A persona (dona Maria, 72 anos, enxerga pouco), o problema (serviço público depende de texto) e os ODS 10 e 16. |
| 0:30–1:10 | Diagrama: microfone → STT → guardas → base de conhecimento → LLM → adaptação para fala → TTS | Cada etapa é um módulo separado e trocável. Quais modelos usamos e por que são locais ou de nuvem: a voz não sai do computador. |
| 1:10–1:40 | Tela de consentimento | A voz é gravada e processada. O que sai da máquina e o que não sai. O áudio é apagado depois de virar texto. Mostrar a marcação do aviso antes de usar. |
| 1:40–3:40 | **Conversa real pelo microfone**, com transcrição, resposta em texto, áudio e latência visíveis | Os turnos da próxima seção. |
| 3:40–4:20 | Tabelas do relatório: WER, acerto do LLM, notas do TTS e latência | A comparação entre duas opções (`base` contra `small` no STT, e os dois LLMs) e a escolha final por qualidade e latência. Usar os números reais, não os sintéticos. |
| 4:20–5:00 | Slide de fechamento | Limitações (base de conhecimento, latência em CPU, viés do STT) e melhorias futuras (sintetizar a primeira frase antes do resto). |

## Turnos da demonstração (1:40–3:40)

Falar de verdade no microfone, sem usar o upload.

1. **Pergunta normal:** "Que horas a UBS abre?" Mostrar a transcrição, a resposta, o áudio e as latências por etapa.
2. **Continuação:** "E o que eu preciso levar lá?" Mostra a memória da conversa. A regra de continuação reconhece palavras como "e" e "lá".
3. **Recusa fora do tema:** por exemplo, "Me ensina uma receita de bolo." O assistente diz que não sabe e encaminha, sem passar pelo LLM.
4. **Opcional:** "Estou com dor no peito." Resposta fixa mandando ligar para 192, 193 ou 190.

## Antes de gravar

- [ ] **Base de conhecimento:** hoje é provisória e fictícia. Se gravar antes de integrar o RAG da pasta 03, dizer isso no vídeo. Depois da integração, trocar as perguntas por fatos reais do corpus de SJC e testar cada uma antes.
- [ ] **Áudio da resposta:** conferir que o som do assistente sai na gravação, não só o microfone.
- [ ] **Aquecimento:** os modelos locais demoram (cerca de 12 s ponta a ponta em CPU). Fazer um turno de teste antes e cortar a espera na edição, ou avisar que a resposta leva alguns segundos.
- [ ] **Dados pessoais:** não falar nome completo, CPF ou endereço reais.
- [ ] **Números do relatório:** usar as medições com gravações reais do grupo, não as preliminares com áudios sintéticos.
- [ ] **Cobertura do critério:** o vídeo precisa mostrar voz entrando, texto e áudio saindo e latência registrada.
