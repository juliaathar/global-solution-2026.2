# Testes e métricas do assistente de voz

Rode tudo a partir de `02-pln-voz/`. Os resultados vão para `evidencias/` (CSV e resumo em Markdown, prontos para virar tabela no relatório).

Os áudios gravados pelo grupo ficam em `audios_teste/`. Eles **não são apagados** pelos scripts, ao contrário do áudio de um usuário real. Só grave quem concordou, e descreva no relatório que são gravações de teste com consentimento.

## O que o enunciado pede e como cobrir

| Componente | Mínimo | Script | Dados |
|---|---|---|---|
| STT | 20 áudios, 3 vozes, 5 com ruído, WER (jiwer) | `testes/avaliar_stt.py` | `audios_teste/manifesto_stt.csv` e `audios_teste/stt/` |
| LLM | 30 perguntas (5 de continuação, 5 fora do escopo) | `testes/avaliar_llm.py` | `testes/perguntas_llm.csv` |
| TTS | 10 respostas, 3 avaliadores, notas de 1 a 5 | `testes/avaliar_tts.py` | `testes/respostas_tts.csv` e `testes/planilha_tts.csv` |
| Ponta a ponta | 10 conversas de 3 turnos ou mais | `testes/avaliar_e2e.py` | `testes/conversas_e2e.csv` e `audios_teste/e2e/` |
| Comparação | duas opções em um componente | `--modelos base small` (STT) ou `--llm` repetido | |

## 0. Validar o pipeline antes das gravações (opcional)

```bash
python testes/gerar_audios_sinteticos.py
python testes/avaliar_stt.py --manifesto audios_teste/sintetico/manifesto.csv --pasta audios_teste/sintetico --saida evidencias/sintetico
```

Gera 20 áudios sintéticos (3 vozes do edge-tts, ruído branco a 10 dB em 5 deles) e mede o WER, só para conferir o script e ter uma medição preliminar. **Não substitui as gravações do grupo**: vozes sintéticas são mais limpas que pessoas reais e não dizem nada sobre sotaque ou idade. Os resultados ficam em `evidencias/sintetico/`, separados dos oficiais.

## 1. STT

1. Grave as 20 frases da coluna `referencia` de `audios_teste/manifesto_stt.csv`, em WAV, com o nome da coluna `arquivo`, na pasta `audios_teste/stt/`. A coluna `falante` já divide em 3 vozes (A, B, C) e `ruido = sim` marca os 5 áudios com ruído de fundo (ligue uma TV, ventilador ou rua).
2. Preencha `faixa_etaria` e `sotaque` de cada gravação. Sem isso a análise de viés só cobre falante e ruído. Inclua, se possível, uma voz de pessoa idosa.
3. Rode:
   ```bash
   python testes/avaliar_stt.py --modelos base small
   ```
   Saída: WER global e médio por modelo, latência média, WER por falante, ruído, faixa etária e sotaque, e as 5 piores transcrições. A normalização escreve números por extenso e junta siglas ("u b s" vira "ubs") dos dois lados, para não punir o modelo por formato.

## 2. LLM

```bash
python testes/avaliar_llm.py --llm ollama:qwen2.5:3b --llm groq:llama-3.1-8b-instant
```

- Cada `conversa` usa uma memória nova, então as perguntas de continuação dependem da pergunta anterior.
- Com o Ollama no ar (`ollama serve`), baixe os modelos (`ollama pull qwen2.5:3b` e `ollama pull qwen2.5:1.5b`). O primeiro uso de cada modelo é lento, porque ele é carregado na memória.
- Para não perder as notas manuais ao rodar outro modelo, use `--anexar`: `python testes/avaliar_llm.py --anexar --llm ollama:qwen2.5:1.5b`.
- Depois de preencher `acerto_manual` (e `obs_manual`) no CSV, recalcule o resumo sem chamar o modelo: `python testes/avaliar_llm.py --so-resumir`.
- `testes/perguntas_fuga.csv` tem 10 conversas de 2 turnos (uma pergunta do tema e outra fora do tema) para medir se a guarda de "não sei" resiste a mudanças de assunto: `python testes/avaliar_llm.py --llm ollama:qwen2.5:3b --perguntas testes/perguntas_fuga.csv --saida evidencias/fuga_depois`. A opção `--saida` mantém esses resultados separados dos oficiais. O modelo varia entre rodadas (temperatura 0,2), então repita as medições antes de comparar.
- `esperado` usa `;` para E e `|` para OU (sem diferença de acento ou caixa). É uma aproximação: leia a lista de erros e, se a resposta estiver certa com outras palavras, escreva `1` em `acerto_manual` em `evidencias/llm_resultados.csv` (ou `0`, para derrubar um acerto falso). A coluna manual prevalece no resumo.
- Os tipos são `normal`, `continuacao`, `fora_escopo` (deve recusar e encaminhar) e `sem_resposta` (tema certo, mas a base não tem o dado, então deve dizer que não sabe).
- **Atenção:** as respostas esperadas foram escritas a partir do corpus provisório de `llm/base_stub.py`, cujos textos são exemplos fictícios. Quando o RAG da pasta 03 existir, troque a base em `componentes.carregar_base()` e revise `perguntas_llm.csv` com os fatos reais.

## 3. TTS

```bash
python testes/avaliar_tts.py gerar --motores edge-tts piper
```

Gera as 10 respostas em `audios_teste/tts/` e a planilha `testes/planilha_tts.csv` com 3 avaliadores por resposta. Cada avaliador ouve e preenche `naturalidade` e `clareza` (inteiros de 1 a 5). Depois:

```bash
python testes/avaliar_tts.py resumir
```

O `gerar` se recusa a sobrescrever uma planilha existente (use `--forcar` só para recomeçar). Troque "Avaliador 1, 2 e 3" pelos nomes ou números reais, mantendo 3 pessoas distintas.

## 4. Ponta a ponta

Grave as 30 falas de `testes/conversas_e2e.csv` (coluna `pergunta_planejada`) em `audios_teste/e2e/`, e rode:

```bash
python testes/avaliar_e2e.py
```

Cada conversa tem pergunta, continuação e um assunto fora do escopo ou sem dado. Mede STT, LLM+RAG, adaptação, TTS e o total. O `total` vai da pergunta até a resposta estar pronta para tocar.

`--demo` roda com módulos falsos, só para conferir o fluxo.

Sem gravações, dá para uma medição preliminar com falas sintéticas: `python testes/gerar_audios_sinteticos.py --e2e` e depois `python testes/avaliar_e2e.py --pasta audios_teste/sintetico_e2e --saida evidencias/sintetico`. Escolha os modelos pelas variáveis `STT_MODEL`, `LLM_PROVIDER`, `LLM_MODEL` e `TTS_ENGINE`. O Ollama deve estar com o modelo carregado antes, para o carregamento não entrar na latência.

## Testes automáticos dos scripts

```bash
python -m unittest discover -s testes -v
```

Cobrem a adaptação para fala, o assistente (guardas e memória), a lógica de cada script de avaliação e conferem que os arquivos de dados cumprem os mínimos do enunciado (30 perguntas, 20 áudios com 3 vozes e 5 ruidosos, 10 conversas de 3 turnos, 10 respostas de TTS). O teste do WER exige `jiwer` e é pulado se ele não estiver instalado.
