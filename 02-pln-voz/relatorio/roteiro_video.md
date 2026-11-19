# Roteiro do vídeo: Assistente de Voz do EloBairro (PLN)

Duração máxima: **5 minutos**. O enunciado exige uma conversa real por voz com pelo menos 3 turnos, incluindo uma pergunta de continuação e uma recusa. O critério "Relatório e vídeo" também avalia problema, persona, ODS, justificativas e a demonstração funcionando.

O roteiro abaixo foi escrito para a demonstração que roda neste Codespace, com a configuração final do relatório: Whisper `small`, `qwen2.5:1.5b` (local) e Piper. Os tempos foram medidos numa conversa de teste feita pela própria interface.

## 1. Antes de filmar (10 minutos)

No terminal do Codespace:

```bash
bash ~/pln_run/demo.sh status      # confere o que está no ar
bash ~/pln_run/demo.sh voz         # sobe o assistente (2 a 4 minutos na primeira vez; aquece o modelo)
```

1. Quando aparecer "Assistente de voz (02) no ar", abra a aba **Portas** (Ports) do VS Code. A porta **7860** aparece sozinha. Clique com o botão direito, "Abrir no navegador" (ou copie o endereço HTTPS).
2. **Ensaio obrigatório:** faça a conversa inteira da seção 3 uma vez, antes de gravar. Isso confirma o microfone e deixa o modelo quente. Depois clique em **Nova conversa** para zerar a memória.
3. Sala silenciosa, sem ventilador nem rádio (nas gravações de teste, o ruído piorou a transcrição).
4. Se o Codespace tiver dormido, rode de novo o `demo.sh voz`.

## 2. Como filmar só com o celular (o PC não precisa gravar a tela)

**Opção A, a mais simples e com o melhor som: abrir o app no próprio celular e gravar a tela dele.**
1. No celular, abra o endereço HTTPS da porta 7860 (o mesmo da aba Portas). A porta é privada: entre com a sua conta do GitHub quando pedir.
2. Permita o microfone ao navegador quando ele perguntar.
3. Abra o gravador de tela do Samsung (painel rápido, arrastando do topo duas vezes) e escolha o som **mídia + microfone**. Faça **um teste de 30 segundos** antes: em alguns aparelhos o navegador e o gravador disputam o microfone. Se sua voz sumir da gravação, grave só os sons de mídia e narre depois em cima do vídeo.
4. A voz da resposta (Piper) toca sozinha, e a transcrição e a tabela de latência aparecem na tela.

**Opção B: filmar o monitor com o celular.** Apoie o celular (de preferência em um tripé) apontado para a tela do PC, fale no microfone do PC e deixe o alto-falante do PC ligado. Funciona, mas o som tende a ficar pior.

## 3. Roteiro por tempo

| Tempo | O que mostrar | O que falar |
|---|---|---|
| 0:00 a 0:25 | O app aberto (tela de consentimento) | "Eu sou o Edgar, e este é o assistente de voz do EloBairro, do nosso projeto da Global Solution. Ele atende a dona Maria, 72 anos, que enxerga pouco e tem dificuldade com texto no celular: ela pergunta falando e ouve a resposta. Ele se liga aos ODS 10, redução das desigualdades, e 16, instituições acessíveis." |
| 0:25 a 1:05 | O diagrama `relatorio/figuras/arquitetura.png` (abra em outra aba pelo GitHub: `https://github.com/juliaathar/global-solution-2026.2/blob/main/02-pln-voz/relatorio/figuras/arquitetura.png`) | "O fluxo é: o microfone, o reconhecimento de fala, as guardas de segurança, a base de conhecimento, o modelo de linguagem, a adaptação para fala e a voz sintética. Cada etapa é um módulo separado e trocável. A base é o RAG com 33 páginas da Prefeitura de São José dos Campos. As guardas tratam emergência e dizem que não sabem, em vez de inventar. Tudo roda no computador: a voz e a pergunta não saem dele." |
| 1:05 a 1:30 | De volta ao app: o **aviso de consentimento** | Leia o aviso em voz alta: "Antes de usar, o app avisa que a voz é gravada e processada, que a transcrição é feita neste computador, que o áudio é apagado depois de virar texto, e que a voz que responde é sintética." Marque a caixa e toque em **Começar**. |
| 1:30 a 3:30 | **Conversa ao vivo** (3 turnos, seção 4) | Veja a seção 4. |
| 3:30 a 4:20 | O README do 02 no GitHub (`https://github.com/juliaathar/global-solution-2026.2/tree/main/02-pln-voz`), na tabela de testes | "Medimos cada componente. No reconhecimento de fala, com 20 gravações nossas, três vozes e cinco com ruído, o Whisper `small` errou bem menos as siglas do que o `base`. No modelo de linguagem, 30 perguntas sobre o corpus real, 82,6% de acertos, com todas as recusas adequadas. Na voz, seis pessoas avaliaram sem saber qual motor era qual, e o Piper empatou com o `edge-tts`, por isso ficamos com o Piper, que roda local." |
| 4:20 a 5:00 | O README ou o relatório | "As limitações: em CPU, uma resposta leva de 30 a 60 segundos, o que não serve para uma pessoa idosa, e precisaria de GPU ou de uma API de nuvem. O reconhecimento erra siglas como CRAS. E não testamos com pessoas idosas. Mas o fluxo completo funciona e respeita a LGPD." |

## 4. A conversa ao vivo: fale exatamente isto

Fale devagar, perto do microfone, com frases completas. Esta sequência foi testada pela interface e funcionou (STT correto nos três turnos).

| Turno | O que você diz | O que o app deve responder | Espera medida |
|---|---|---|---|
| **1** | "Quem pode usar o transporte adaptado?" | Pessoas com deficiência motora, mental ou múltipla severa, que precisam de alto grau de dependência e não podem usar o transporte coletivo urbano. | **cerca de 67 s** (a maior parte é o modelo) |
| **2, continuação** | "E esse serviço é gratuito?" | "Sim, o transporte adaptado é gratuito." (ele entendeu o assunto pela memória da conversa) | cerca de 37 s |
| **3, recusa** | "Como tirar passaporte?" | "Não tenho essa informação com segurança. Posso ajudar com serviços públicos do bairro..." | cerca de 6 s |
| 4, opcional | "Estou com dor no peito." | "Isso parece uma emergência. Ligue agora para o 192, que é o SAMU, para o 193, dos Bombeiros, ou para o 190, da Polícia. Não espere." (a guarda de emergência não passa pelo modelo) | cerca de 5 s (testado pela interface) |

**Como usar a espera no vídeo.** O turno 1 leva mais de 1 minuto. Duas saídas:
- **Narrar enquanto espera:** "Estamos rodando em CPU, sem placa de vídeo. Aqui na tabela vemos o tempo de cada etapa: o reconhecimento de fala leva uns 5 segundos, a voz 1 segundo, e o resto é o modelo de linguagem lendo os trechos da base." Isso mostra a **latência por etapa**, que o enunciado pede.
- **Cortar a espera na edição** do próprio celular, deixando uma legenda "tempo real: 67 s".

Mostre na tela, a cada turno: a **transcrição** (o que o assistente ouviu), a **resposta em texto** e a **tabela de latência** (colunas STT, LLM+RAG, adaptação, TTS e total).

## 5. Números para citar (todos do relatório)

- Reconhecimento de fala: 20 gravações, 3 vozes, 5 com ruído. WER das conversas: `small` 0,126 contra `base` 0,201. O `small` leva cerca de 5 s por áudio, contra 1,5 s do `base`.
- Modelo de linguagem: 30 perguntas com o RAG real, 82,6% de acertos nos dois modelos (revisão assistida por IA, com amostra conferida por um integrante). O `1.5b` leva metade do tempo do `3b`.
- Voz: avaliação cega por 6 pessoas em 3 duplas, nota geral de 4,26 (Piper) contra 4,30 (`edge-tts`), em escala de 1 a 5.
- Latência da pergunta ao início da fala: 17,8 s em média na configuração local; de 34 a 64 s nos turnos que chamam o modelo; de 3 a 7 s nos que a guarda resolve.

## 6. Se algo der errado

| Problema | O que fazer |
|---|---|
| O app não abre | `bash ~/pln_run/demo.sh status` e, se preciso, `bash ~/pln_run/demo.sh voz` |
| Resposta passando de 2 minutos | Clique em **Nova conversa** e repita o turno. Se repetir, rode `demo.sh voz` de novo (reaquece o modelo) |
| O assistente ouviu errado | Fale mais devagar, de perto, e repita. É o ponto fraco do reconhecimento de fala e pode virar um comentário honesto no vídeo |
| O Codespace dormiu | O app para junto. Reabra o Codespace e rode `demo.sh voz` |
| Quer respostas em segundos | `bash ~/pln_run/demo.sh voz-nuvem` usa o LLM da OpenAI do `.env` (resposta em 1 a 3 s). O aviso de consentimento passa a dizer que o texto da pergunta vai à OpenAI, e isso foge da configuração local do relatório |

## 7. Opcional: mostrar o sistema integrado (o front da `main`)

Se sobrar tempo, o `bash ~/pln_run/demo.sh front` sobe a interface integrada (Streamlit na porta 8501, API na 8000). **Ele para o app de voz**, porque os dois juntos não cabem na memória do Codespace. A aba "Falar" do front faz só um turno por vez (sem memória), então ela não serve para a pergunta de continuação: use o app do 02 para a conversa e o front só para mostrar a integração.
