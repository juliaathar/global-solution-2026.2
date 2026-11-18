# Assistente de Voz do EloBairro

**Disciplina:** Processamento de Linguagem Natural e Chatbots (PLN), Global Solution 2026.2, FIAP (CitizenTech)

| Nome completo | RM |
|---|---|
| Bruno Fernandes Nascimento | 552574 |
| Edgar Lódula de Assis | 565260 |
| Júlia Aben-Athar | 566325 |

**Repositório:** [PREENCHER: link do GitHub]  
**Vídeo (até 5 min):** [PREENCHER: link]  
**Data:** [PREENCHER]

> **Como usar este esqueleto.** Cada seção tem um bloco "Escrever" com o que o enunciado pede, um texto "Já temos" apoiado no que existe no repositório, e marcadores `[PREENCHER: ...]` para o que só o grupo sabe ou só os testes mostram. Apague os blocos "Escrever" antes de exportar. As tabelas de resultado entram sozinhas depois que os scripts de `testes/` rodarem (veja `relatorio/README.md`). Escrevam a conclusão com as próprias palavras.

---

## 1. Introdução: problema e persona

> **Escrever:** a persona atendida, o problema que o assistente resolve e por que a voz é o canal certo. Cite fontes (dados, notícias ou relatos) que sustentem o problema.

**Persona.** [PREENCHER: confirmar ou trocar a persona proposta no README: dona Maria, 72 anos, enxerga pouco e tem dificuldade com texto no celular, prefere perguntar falando e ouvir a resposta.]

**Problema.** Os canais de serviço público dependem de texto, cadastro e linguagem burocrática. Idosos, pessoas com baixa alfabetização e pessoas com deficiência visual ou motora ficam de fora. O assistente permite perguntar por voz sobre serviços do bairro (UBS, CRAS, segunda via de documentos, problemas na rua) e ouvir a resposta em linguagem simples.

**Evidência do problema.** [PREENCHER: dados e fontes com URL e data de consulta, por exemplo sobre analfabetismo funcional, população idosa e pessoas com deficiência visual no Brasil. O README da raiz prevê reunir essas fontes em `docs/problema-publico.md`.]

**Escopo.** O assistente faz parte do EloBairro, que reúne nove disciplinas. Este relatório cobre só o módulo de voz: STT, LLM com memória e base de conhecimento, adaptação para fala e TTS.

## 2. ODS relacionados

> **Escrever:** o ODS e como o assistente contribui. Conferir a redação das metas no texto oficial da ONU antes de citar.

O projeto se relaciona com o **ODS 10** (redução das desigualdades) e o **ODS 16** (paz, justiça e instituições eficazes).

- ODS 10: [PREENCHER: meta e justificativa, por exemplo a inclusão de pessoas que hoje não conseguem usar interfaces de texto (meta 10.2, conferir).]
- ODS 16: [PREENCHER: meta e justificativa, por exemplo o acesso à informação pública e instituições acessíveis (metas 16.6 e 16.10, conferir).]

## 3. Arquitetura

> **Escrever:** o diagrama, o fluxo de um turno e o papel de cada módulo. Mostre que cada etapa é separada e trocável.

![Arquitetura do assistente de voz](figuras/arquitetura.png)

[PREENCHER: exportar o diagrama Mermaid do `README.md` da pasta 02 para `relatorio/figuras/arquitetura.png`.]

Fluxo de um turno: o áudio (microfone ou arquivo) é transcrito pelo STT; as guardas verificam emergência e se há contexto; o RAG recupera trechos; o LLM responde com o system prompt e o histórico; a adaptação deixa o texto pronto para fala; o TTS gera o áudio. O tempo de cada etapa é registrado.

| Etapa | Módulo | Opções implementadas |
|---|---|---|
| Captura | `app.py` | microfone e upload, com aviso de consentimento |
| STT | `stt/` | faster-whisper `base` e `small` |
| Guardas e memória | `llm/assistente.py` | emergência e "não sei" sem passar pelo LLM; últimos 6 turnos |
| LLM | `llm/provedores.py` | Ollama (local), Groq e Gemini (nuvem) |
| Base de conhecimento | `componentes.py` | [PREENCHER: RAG da pasta 03; hoje há uma base provisória] |
| Adaptação para fala | `adaptacao_fala/` | sem markdown e emoji, frases curtas, números, siglas, valores, datas e horas por extenso |
| TTS | `tts/` | Piper (local) e edge-tts (nuvem) |
| Latência | `pipeline.py` | STT, LLM+RAG, adaptação, TTS e total |

## 4. Justificativa das escolhas

> **Escrever:** por que nuvem ou local (custo, latência, privacidade, disponibilidade de internet), por que RAG, e por que cada modelo. A escolha final de modelos deve apoiar-se nas medições da seção 6.

### 4.1 Nuvem ou local

| Etapa | Escolha | Motivo |
|---|---|---|
| STT | local (faster-whisper) | a voz do usuário não sai do computador |
| LLM | local (Ollama), na medição preliminar | mantém a pergunta no computador; em CPU, sem GPU, o Qwen 3B levou de 6,5 a 8,0 s por chamada (seção 6.2), o que pesa na latência |
| TTS | [PREENCHER: Piper ou edge-tts, depois da avaliação de naturalidade e clareza] | edge-tts envia o texto da resposta à Microsoft e precisa de internet; Piper roda no computador. Na medição preliminar, o Piper sintetizou em 1,13 s em média contra 2,31 s do edge-tts (seção 6.3) |

O STT e o Piper rodam no computador, sem custo por uso. O edge-tts não exigiu chave de API neste projeto, mas depende de internet. O LLM local também não tem custo por uso, mas exige cerca de 2 GB de disco para o modelo 3B.

### 4.2 Por que RAG

As informações do domínio (horários, documentos exigidos, benefícios) mudam e precisam ser confiáveis. Com RAG, o conteúdo fica em uma base que se atualiza sem retreinar, o LLM responde só com trechos recuperados, e cada resposta pode ser rastreada até uma fonte. Fine-tuning exigiria dados e GPU e deixaria a informação congelada no modelo; colocar todo o conteúdo no prompt não cabe quando a base cresce. [PREENCHER: corpus usado, fontes e quantidade de trechos, vindos da pasta 03.]

### 4.3 Modelos, versões e licenças

Versões usadas nas medições (a tabela completa, com licenças, está no `README.md` da pasta 02):

| Componente | Versão | Licença |
|---|---|---|
| faster-whisper | 1.2.1 (CTranslate2 4.9.0, PyAV 16.1.0) | MIT |
| Pesos Whisper `base` e `small` | convertidos pelo projeto Systran para CTranslate2 | MIT (Whisper) |
| Piper (`piper-tts`) | 1.8.0 | GPL-3.0 ou posterior |
| Voz Piper `pt_BR-faber-medium` | n/d | CC0 (dataset, segundo o cartão da voz) |
| edge-tts | 7.3.1 | LGPL-3.0, usa o serviço online do Edge |
| LLM `qwen2.5:3b` via Ollama | Ollama 0.40.16 | licença Qwen Research (a conferir no cartão do modelo) |
| LLM `qwen2.5:1.5b` via Ollama | Ollama 0.40.16 | a conferir no cartão do modelo |

## 5. Metodologia dos testes

> **Escrever:** como os dados de teste foram produzidos, para que alguém consiga repetir. Os mínimos do enunciado estão na tabela.

| Componente | Teste mínimo | Métrica |
|---|---|---|
| STT | 20 áudios do grupo, 3 vozes, 5 com ruído de fundo | WER com `jiwer` |
| LLM | 30 perguntas com resposta esperada (5 de continuação, 5 fora do escopo) | % corretas e % de recusas adequadas |
| TTS | 10 respostas avaliadas por 3 pessoas | naturalidade e clareza, de 1 a 5 |
| Ponta a ponta | 10 conversas de 3 turnos ou mais | latência por etapa e total |

- **Áudios do STT:** o enunciado pede 20 áudios gravados pelo grupo. [PREENCHER: quem gravou, quantas vozes, idade e sotaque, aparelho, ambiente, fonte do ruído de fundo e a confirmação de que todos consentiram.] Enquanto essas gravações não existem, fizemos uma **medição preliminar com 20 áudios sintéticos**: as mesmas 20 frases lidas por três vozes do edge-tts (Francisca, Antonio e Thalita), com ruído branco a 10 dB de relação sinal-ruído em 5 deles (`testes/gerar_audios_sinteticos.py`). Vozes sintéticas são mais limpas que pessoas reais, então esses números tendem a ser mais otimistas e não dizem nada sobre sotaque ou idade.
- **Perguntas do LLM:** 30 perguntas (18 normais, 5 de continuação, 5 fora do escopo e 2 sem resposta na base), com palavras-chave esperadas. Foram escritas a partir da base provisória de 4 textos, que são exemplos fictícios. A correção automática confere palavras-chave; as respostas foram lidas uma a uma, e a revisão manual preliminar (feita com assistência de IA, a conferir pelo grupo) está em `evidencias/llm_resultados.csv`, nas colunas `acerto_manual` e `obs_manual`.
- **Avaliação do TTS:** [PREENCHER: quem avaliou, em que condições de escuta, e se os avaliadores sabiam qual motor estavam ouvindo.]
- **Equipamento das medições:** Intel Core i5-6300U (2 núcleos, 4 threads), 16 GB de RAM, sem GPU, Windows 10, Python 3.13. O STT rodou localmente em CPU com `int8`; o edge-tts usou a internet. O LLM rodou localmente pelo Ollama 0.40.16 (`qwen2.5:3b` e `qwen2.5:1.5b`), em CPU. A rede só foi usada pelo edge-tts.

## 6. Resultados

> **Escrever:** depois de cada tabela, uma análise curta: o que os números mostram, onde o sistema errou e por quê. Use os erros listados nos resumos.

### 6.1 STT

<!-- INCLUIR: evidencias/stt_resumo.md -->

[PREENCHER: análise do resultado com as gravações reais do grupo.]

**Medição preliminar com áudios sintéticos.**

<!-- INCLUIR: evidencias/sintetico/stt_resumo.md -->

O `small` errou menos que o `base`: WER global de 0,066 contra 0,114, uma redução de cerca de 42% nos erros, mas levou 6,86 s por áudio contra 2,11 s (cerca de 3,3 vezes mais) nesta CPU, na média das 20 chamadas. O ruído branco a 10 dB não piorou o `base` (0,137 contra 0,138 sem ruído) e piorou pouco o `small` (0,087 contra 0,060), mas são só 5 áudios ruidosos, o que é pouco para concluir. Os erros se concentram em siglas e palavras curtas: o `base` transcreveu "UBS" como "B.S." e "ao BS", e o `small` trocou "como eu aviso" por "com o meu aviso". Como as siglas aparecem em várias perguntas do domínio, isso merece atenção na escolha do modelo.

### 6.2 LLM e diálogo

<!-- INCLUIR: evidencias/llm_resumo.md -->

**Guardas, medidas sem LLM.** Primeiro medimos o que não depende do modelo, usando um LLM de teste que só sinaliza quando é chamado e a base provisória de 4 textos:

| Tipo de pergunta | Perguntas | Resultado da guarda |
|---|---|---|
| Fora do escopo | 5 | 5 recusadas pela guarda, sem chamar o LLM |
| Normais | 18 | 18 enviadas ao LLM (nenhuma recusada indevidamente) |
| Continuação | 5 | 5 enviadas ao LLM |
| Sem resposta na base | 2 | 2 enviadas ao LLM: dependem de ele admitir que não sabe |

Esses números valem para a base provisória. Com o RAG real, que terá mais conteúdo, uma pergunta fora do tema pode recuperar algum trecho e passar pela guarda, então o teste precisa ser repetido [PREENCHER: com o RAG da pasta 03]. A detecção de emergência acertou 5 de 7 frases de teste e errou "meu vizinho está passando mal" e "tem alguém sendo agredido na rua". Ampliamos a lista de padrões depois de ver esses erros, então o resultado atual não é uma medição independente.

**Resultado com os modelos reais** (base provisória, CPU, acima). O `qwen2.5:3b` acertou 21 de 23 perguntas que dependem do modelo (91,3%), contra 14 de 23 (60,9%) do `qwen2.5:1.5b`. Na continuação, 4 de 5 contra 2 de 5. O 1.5B inventou informações ("No centro da cidade", "Não há custo para isso") e contradisse a base ao dizer que o EloBairro não gera número de acompanhamento. O 3B errou a q08 (mandou levar "o RG" para tirar a segunda via do RG) e a q17 (disse que certidão de casamento não serve e, na frase seguinte, mandou levar certidão de casamento).

A correção automática marcou a q17 como acerto nos dois modelos, só por conter a palavra-chave. Por isso as respostas foram lidas uma a uma, e a revisão manual preliminar (feita com assistência de IA, a conferir pelo grupo) está na coluna `acerto_manual`.

Os 100% de recusa fora do escopo precisam de ressalva: as 5 recusas vieram da guarda, sem passar pelo modelo. Nas 2 perguntas sem resposta na base, o 3B disse que não sabia nas duas, e o 1.5B inventou "não há custo" em uma (50%). A latência por chamada ao LLM foi de 8,03 s no 3B e 6,22 s no 1.5B.

**Variação entre rodadas.** O `qwen2.5:3b` foi medido três vezes nas mesmas 30 perguntas, e a revisão manual deu 91,3% (21 de 23), 87,0% (20 de 23) e 82,6% (19 de 23). Verificamos que os trechos recuperados são idênticos nas três rodadas para as 25 perguntas que dependem do modelo, então a diferença vem do próprio modelo (temperatura 0,2), sobretudo em perguntas de sim ou não sobre a base, em que ele às vezes se contradiz (q14 e q17 na última rodada). Um único percentual, portanto, não é estável. [PREENCHER: repetir a medição com temperatura 0 ou com mais rodadas e informar a média.]

**Fuga da guarda em perguntas de continuação.** No ponta a ponta, um pedido de piada logo depois de uma pergunta sobre a UBS foi atendido pelo LLM. A causa era que, sem contexto para a pergunta sozinha, a busca a unia à pergunta anterior, encontrava o contexto da UBS e a guarda de "não sei" nunca disparava. Montamos 10 casos (uma pergunta do tema seguida de uma fora do tema, em `testes/perguntas_fuga.csv`) e medimos antes e depois:

| Versão | Barrados pela guarda | Recusados pelo modelo | Atendidos fora do escopo |
|---|---|---|---|
| Antes da correção | 0 | 4 | 6 |
| Só a regra de continuação | 7 | 1 | 2 |
| Regra, checagem de assunto e palavras vazias | 10 | 0 | 0 |

Pelo critério automático, no caso do vizinho barulhento o modelo deu um conselho e encaminhou à Defensoria, e isso entrou como "atendido". A regra final reaproveita a pergunta anterior só se a fala parecer continuação (começa com "e", "mas" ou "então", ou usa "isso", "ela", "lá" e palavras parecidas) **e** dividir alguma palavra com a conversa anterior. Os dois furos da versão intermediária foram "E me conta uma piada?", que parecia continuação, e um pedido de poema, que casava com a palavra "sobre" do texto do CRAS. As 5 continuações do conjunto de 30 perguntas seguem funcionando. O custo é que continuações legítimas com vocabulário novo ("E se eu não tiver?") agora recebem "não tenho essa informação". A regra foi ajustada com os mesmos casos usados para medir, então o 10 de 10 é otimista. [PREENCHER: testar com falas novas escritas pelo grupo.]

### 6.3 TTS

<!-- INCLUIR: evidencias/tts_resumo.md -->

As notas de naturalidade e clareza ainda não existem. Os 20 áudios (10 respostas, 2 motores) estão em `audios_teste/tts/` e a planilha dos 3 avaliadores está pronta em `testes/planilha_tts.csv`. [PREENCHER: notas médias e comentários dos avaliadores.]

O que já foi medido é o tempo de síntese neste computador:

| Motor | Respostas | Síntese média (s) | Mínima (s) | Máxima (s) |
|---|---|---|---|---|
| edge-tts (nuvem) | 10 | 2,31 | 1,73 | 4,25 |
| Piper `pt_BR-faber-medium` (local) | 10 | 1,13 | 0,59 | 4,99 |

O Piper foi mais rápido em média e roda sem internet. Os 4,99 s do máximo dele podem incluir a primeira chamada, o que não foi verificado. O tempo do edge-tts depende da rede.

### 6.4 Ponta a ponta e latência

<!-- INCLUIR: evidencias/e2e_resumo.md -->

**Medição preliminar com falas sintéticas.** Foram 10 conversas de 3 turnos (30 turnos). As falas planejadas foram sintetizadas com as três vozes do edge-tts, sem ruído, porque as gravações do grupo ainda não existem. A configuração foi 100% local, em CPU: Whisper `small`, Qwen 2.5 3B via Ollama e Piper. O modelo do LLM foi carregado antes de começar, então o tempo de carregamento não entra na conta.

<!-- INCLUIR: evidencias/sintetico/e2e_resumo.md -->

A pergunta levou em média 12,1 s até o início da fala, com máximo de 18,6 s. O STT é a etapa mais pesada (6,5 s, cerca de metade do total), seguido do LLM (4,5 s). A adaptação não pesa e o Piper levou 1,1 s. O LLM foi chamado em 19 dos 30 turnos; nos outros 11, a guarda respondeu na hora. Na primeira medição, antes da correção da fuga da guarda (seção 6.2), o total foi de 14,2 s (máximo de 25,0 s), com o LLM chamado em 24 turnos. A média caiu porque a guarda passou a responder mais turnos sem o modelo, e não porque o sistema ficou mais rápido. Na medição isolada do STT, o `base` levou 2,1 s contra 6,9 s do `small`, então trocá-lo reduziria a espera, ao custo de mais erros de transcrição. Para uma pessoa que espera a resposta falada, 12 s ainda é um tempo longo. [PREENCHER: avaliação do grupo sobre se esse tempo é aceitável para a persona, e a medição com as gravações reais.]

**O que a leitura das respostas mostrou.** O script mede tempo, não correção, mas as respostas mostram o comportamento do sistema:

- O pedido de piada ("Obrigado! Me conta uma piada!"), que na primeira medição foi atendido com uma piada, passou a cair na guarda depois da correção (seção 6.2).
- Duas continuações legítimas passaram a receber "não tenho essa informação": "E se eu não tiver?" e "e precisa de mais alguma coisa?". Antes elas recebiam respostas que a base não sustentava ou do assunto errado. A guarda é honesta, mas recusa continuações que usam vocabulário novo.
- Uma continuação ainda trouxe o trecho errado: "E quais documentos eu levo?" depois da pergunta do RG recebeu os documentos da UBS.
- O STT errou palavras nas falas sintéticas ("Como faça a segunda via", "cartão dos SUS para ir ao BS").

### 6.5 Comparação e escolha final

> **Escrever:** a comparação de pelo menos duas opções em um componente (por exemplo Whisper `base` contra `small`), e a decisão com base em qualidade e latência.

Comparação preliminar de STT (20 áudios sintéticos, CPU):

| Modelo | WER global | Latência média (s) |
|---|---|---|
| faster-whisper `base` | 0,114 | 2,11 |
| faster-whisper `small` | 0,066 | 6,86 |

O `small` erra cerca de 42% menos e custa cerca de 3,3 vezes mais tempo. A decisão depende de quanto a latência pesa frente à precisão para a persona. No TTS, o Piper foi mais rápido (1,13 s contra 2,31 s) e a escolha também depende das notas de naturalidade.

Comparação de LLM (30 perguntas, base provisória, CPU):

| Modelo | % corretas | % continuação | % abstenção | Latência por chamada |
|---|---|---|---|---|
| `qwen2.5:3b` | 82,6% a 91,3% (3 rodadas) | 80% | 100% | 6,5 a 8,0 s |
| `qwen2.5:1.5b` | 60,9% | 40% | 50% | 6,22 s |

A escolha preliminar de LLM é o `qwen2.5:3b`: a diferença de tempo por chamada (de 0,2 a 1,8 s) não compensa a queda de qualidade do 1.5B, que inventou respostas. O 1.5B foi medido uma vez, antes da correção da fuga, que não altera a busca dessas perguntas.

[PREENCHER: escolha final de STT e TTS com as gravações reais e as notas dos avaliadores, e a confirmação do LLM.]

## 7. Ética, segurança e LGPD

> **Escrever:** cada cuidado do enunciado, como foi implementado e como foi verificado.

| Cuidado | O que o sistema faz | Como foi verificado |
|---|---|---|
| Consentimento | a interface só libera o uso depois de o usuário marcar que leu o aviso, que diz o que é gravado e o que sai do computador | [PREENCHER: print da tela de aviso] |
| Retenção mínima | o áudio do usuário é apagado logo após a transcrição; só as 5 últimas respostas sintetizadas ficam em disco; o log de latência guarda só números | verificado em um turno real com Whisper e com os dois TTS: o arquivo de áudio de entrada deixou de existir depois da transcrição |
| Uso de nuvem | o áudio nunca é enviado; com LLM em nuvem o texto da pergunta é enviado, e com edge-tts o texto da resposta é enviado; o aviso informa isso | [PREENCHER] |
| Limites do assistente | recusa fora do tema, não dá diagnóstico nem parecer jurídico, encaminha emergência para 192, 193 e 190 | as 5 perguntas fora do escopo foram recusadas pela guarda (seção 6.2), com a base provisória. Um pedido de piada feito logo depois de uma pergunta do tema chegou a ser atendido pelo LLM; depois da correção da seção 6.2, os 10 casos de fuga foram barrados |
| Alucinação | sem trecho recuperado, o LLM nem é chamado e a resposta diz que não sabe | sem trecho recuperado, a guarda responde que não sabe (5 de 5 perguntas fora do escopo). As 2 perguntas sem resposta na base chegaram ao LLM: o `qwen2.5:3b` respondeu que não sabia nas duas (q29 e q30); o `qwen2.5:1.5b` inventou "não há custo" na q30 |
| Clonagem de voz | só vozes sintéticas prontas | voz `pt_BR-faber-medium` do Piper e vozes do edge-tts |

### 7.1 Análise de viés do STT

> **Escrever:** diferenças de erro entre sotaques, idades e ruído, e o que isso significa para a persona.

Na medição preliminar (vozes sintéticas), o WER variou entre as três vozes. No `base`: 0,208 (Francisca), 0,141 (Antonio) e 0,052 (Thalita). No `small`: 0,098, 0,082 e 0,012. Há diferença de desempenho até entre vozes sintéticas, com apenas 6 ou 7 áudios por voz, o que mostra a necessidade de testar com falantes variados. Vozes sintéticas não representam sotaques regionais nem a fala de pessoas idosas, então essa análise **não** cobre o viés que o enunciado pede.

[PREENCHER: tabelas de WER por falante, ruído, faixa etária e sotaque com as gravações reais (vêm do `stt_resumo.md`), a interpretação e o limite da análise, que cobre só as vozes gravadas pelo grupo.]

## 8. Limitações e melhorias futuras

> **Escrever:** o que o sistema ainda não faz bem. Seja específico e honesto, e ligue cada limite a uma melhoria.

**Limitações já conhecidas** (revisar com os resultados reais):

- A base de conhecimento depende do RAG da pasta 03. [PREENCHER: estado final da integração.]
- A correção automática do LLM confere palavras-chave, uma aproximação da qualidade real da resposta: ela marcou como acerto uma resposta que se contradizia (q17).
- A regra que decide se uma fala é continuação é lexical e foi ajustada com os mesmos casos usados para medir. Ela pode recusar uma continuação legítima com vocabulário novo ("E se eu não tiver?") e precisa ser validada com falas novas.
- A continuação ainda pode trazer o trecho errado: em 1 das 10 conversas, a pergunta sobre o RG recebeu os documentos da UBS.
- O `qwen2.5:3b` contradiz a base em perguntas de sim ou não (q14 e q17 na última rodada), e o resultado varia entre rodadas (82,6% a 91,3%).
- A latência média de 12,1 s, em CPU e sem GPU, é alta para quem espera uma resposta falada.
- A guarda de emergência usa uma lista de palavras, então frases fora dela seguem para o LLM.
- A síntese não é em streaming: a fala só começa com a resposta inteira sintetizada.
- O STT erra siglas do domínio: nas medições preliminares, o `base` transcreveu "UBS" como "B.S.".
- Os testes de STT cobrem só as vozes do grupo, então sotaques e faixas etárias não gravados não foram avaliados.
- [PREENCHER: outras limitações observadas nos testes.]

**Melhorias futuras:**

- Sintetizar e tocar a primeira frase antes do resto, para reduzir o tempo até a fala.
- Usar GPU, ou o Whisper `base`, ou um LLM em nuvem para reduzir a latência.
- Trocar a regra lexical de continuação pela relevância (score) da busca do RAG real, exigir uma relevância mínima dos trechos, fixar a temperatura em 0 e repetir cada teste algumas vezes.
- Testar um LLM maior ou em nuvem, que tendem a contradizer menos a base.
- Passar os termos do domínio (UBS, CRAS, SUS) como dica ao Whisper, para reduzir erros em siglas. É uma hipótese ainda não testada.
- Detecção de voz para falar sem apertar botão.
- Avaliação com mais vozes, em especial de pessoas idosas e de sotaques regionais diversos.
- [PREENCHER: melhorias que surgirem das análises da seção 6.]

## 9. Conclusão

> **Escrever:** com as palavras do grupo, o que foi construído, o que os testes mostraram e o que ficou para depois. Evite repetir a introdução.

> **Rascunho.** Este texto foi redigido com base no que o projeto já tem e deixa os números e os resultados para o grupo. Leiam, ajustem o tom e troquem cada `[PREENCHER]` pelo valor medido. Se algum trecho não refletir o que vocês viram nos testes, reescrevam.

Construímos um assistente de voz em português que recebe a pergunta falada, transcreve, responde com apoio de uma base de conhecimento e devolve a resposta em áudio, mostrando também o texto na tela. O objetivo era dar a quem tem dificuldade com interfaces de texto uma forma de perguntar sobre serviços do bairro falando e de ouvir a resposta em linguagem simples. Cada etapa (STT, LLM com memória e base de conhecimento, adaptação para fala e TTS) é um módulo separado, o que permitiu comparar opções, como o Whisper `base` e o `small` no STT e o Piper e o edge-tts no TTS, sem reescrever o resto do sistema.

Os testes preliminares, feitos com áudios sintéticos porque as gravações do grupo ainda não existem, mostraram que o `small` reduz o WER de 0,114 para 0,066 em relação ao `base`, ao custo de cerca de 3,3 vezes mais tempo de transcrição em CPU. Na síntese, o Piper levou em média 1,13 s por resposta e o edge-tts 2,31 s. [PREENCHER: resultado do STT com as gravações reais do grupo.] No diálogo, o `qwen2.5:3b` acertou entre 82,6% e 91,3% das perguntas que dependem do modelo em três rodadas (4 de 5 nas de continuação), contra 60,9% do `qwen2.5:1.5b` em uma rodada, e as recusas fora do escopo vieram da guarda. Na avaliação do TTS, a nota média foi [PREENCHER] em naturalidade e [PREENCHER] em clareza. A latência média da pergunta até o início da fala foi de 12,1 s na configuração local testada (preliminar, em CPU), e a etapa que mais pesou foi o STT, com 6,5 s. Com isso, escolhemos [PREENCHER: modelos finais] porque [PREENCHER: razão com base em qualidade e latência].

Duas decisões de projeto pesaram mais do que a escolha dos modelos. A primeira foi manter a transcrição no computador do usuário, de modo que a voz, que é um dado pessoal, não seja enviada a nenhum serviço externo. A segunda foi tratar emergências e ausência de informação com respostas fixas, fora do LLM, em vez de depender só do system prompt para que o modelo recuse ou admita que não sabe. Nos testes, a guarda barrou as 5 perguntas fora do escopo sem chamar o LLM, mas a detecção de emergência falhou em 2 de 7 frases na primeira versão e foi ampliada. O `qwen2.5:3b` disse que não sabia nas duas perguntas sem resposta na base, mas, no ponta a ponta, um pedido de piada feito depois de uma pergunta do tema passou pela guarda e foi atendido. Corrigimos a regra de continuação e os 10 casos de fuga passaram a ser barrados, embora a correção tenha sido ajustada com os mesmos casos da medição.

O trabalho tem limites que precisam ficar claros. [PREENCHER: estado final da base de conhecimento e da integração com o RAG.] Os áudios de teste foram gravados por [PREENCHER: número] pessoas do grupo, então a análise de viés não cobre sotaques e faixas etárias que não gravamos, em especial a voz de pessoas idosas, que é o público principal. A correção automática das respostas do LLM confere palavras-chave e foi complementada por uma revisão manual das 60 respostas (preliminar, feita com assistência de IA, a conferir pelo grupo). Como a síntese de voz não é em streaming, a fala só começa quando a resposta inteira está pronta.

Como próximos passos, propomos sintetizar e tocar a primeira frase antes do resto para reduzir a espera, testar com mais vozes e sotaques, e alimentar a base de conhecimento com fontes oficiais atualizadas. Para a persona que motivou o projeto, [PREENCHER: avaliação do grupo sobre se o tempo de resposta, a clareza da voz e as recusas são adequados para uma pessoa idosa, com base no teste e no vídeo].

## 10. Referências

[PREENCHER: lista com autor, título, URL e data de acesso. Sugestões de itens a citar: o artigo do Whisper (Radford et al., 2022, "Robust Speech Recognition via Large-Scale Weak Supervision"), os repositórios do faster-whisper, do Piper e do edge-tts, a biblioteca jiwer, os textos oficiais dos ODS 10 e 16, a Lei Geral de Proteção de Dados (Lei 13.709/2018) e as fontes do corpus e do problema.]

## Anexos

- Código e README: [PREENCHER: link do repositório, pasta `02-pln-voz`].
- Material de teste: `audios_teste/`, `testes/perguntas_llm.csv`, `testes/planilha_tts.csv`, `testes/conversas_e2e.csv`.
- Resultados brutos: `evidencias/`.
