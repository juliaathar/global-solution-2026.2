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

## Quando as gravações chegarem: organizar

1. Copie os áudios originais (qualquer formato: m4a, opus do WhatsApp, mp3, wav) para `audios_teste/entrada/` (pasta fora do git). Se o nome do arquivo for o código da frase (`stt_01`, `c03_t2`...), nada mais é preciso; senão, copie `audios_teste/modelos/mapeamento.csv` para lá e preencha `original,codigo`.
2. Copie `audios_teste/modelos/vozes.csv` para `audios_teste/entrada/` e preencha, para cada voz A, B e C, a faixa etária, o sotaque e `consentimento` = `sim`. Voz sem consentimento registrado não é processada.
3. Confira sem gravar nada: `python testes/organizar_audios.py --so-conferir`. Ele aponta arquivo sem código, voz sem dados, áudio mudo, curto, longo ou estourado, e ruído marcado que não parece ruidoso.
4. Organize: `python testes/organizar_audios.py`. Converte para WAV 16 kHz mono em `audios_teste/stt/` e `audios_teste/e2e/`, preenche `faixa_etaria` e `sotaque` no `manifesto_stt.csv` e grava `evidencias/audios_qualidade.csv`. Os originais não são alterados.
5. Rode os testes das seções 1 e 4 abaixo. Transcrições muito diferentes da frase indicam arquivo trocado: confira o mapeamento antes de aceitar o WER.

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
- **Base de conhecimento:** o padrão agora é o RAG da pasta 03 (`BASE_CONHECIMENTO=rag`), e `perguntas_llm.csv`, `perguntas_fuga.csv` e `conversas_e2e.csv` foram escritos com fatos do corpus oficial de SJC (cada palavra esperada foi conferida no texto da página). Os arquivos `*_base_ficticia.csv` guardam as perguntas antigas, escritas para a base fictícia; para reproduzir os resultados antigos use `BASE_CONHECIMENTO=stub` e `--perguntas testes/perguntas_llm_base_ficticia.csv`.
- **Como reproduzir a avaliação do LLM (base real):** com o Ollama no ar (`ollama serve`) e os modelos baixados (`ollama pull qwen2.5:3b` e `ollama pull qwen2.5:1.5b`), rode a partir de `02-pln-voz/`:
  ```bash
  export LLM_TIMEOUT_S=900 OLLAMA_URL=http://127.0.0.1:11434   # em CPU o modelo frio leva mais de 2 minutos para responder
  python testes/avaliar_llm.py --retomar --llm ollama:qwen2.5:3b
  python testes/avaliar_llm.py --retomar --llm ollama:qwen2.5:3b --perguntas testes/perguntas_fuga.csv --saida evidencias/fuga_rag
  python testes/avaliar_llm.py --retomar --llm ollama:qwen2.5:1.5b
  ```
  O progresso é gravado após cada pergunta e `--retomar` continua de onde parou (conversas já concluídas e sem erro são puladas), então uma interrupção não perde o trabalho. Uma falha do LLM numa pergunta vira um resultado com `motivo` "erro" e a rodada segue. Aqueça o modelo antes de medir (uma chamada qualquer), para o carregamento não entrar na latência. Depois leia as respostas contra as páginas e preencha `acerto_manual`; `--so-resumir` recalcula o resumo.

## 3. TTS

```bash
python testes/avaliar_tts.py gerar --motores edge-tts piper
```

Gera as 10 respostas em `audios_teste/tts/` e a planilha `testes/planilha_tts.csv` com 3 avaliadores por resposta. Cada avaliador ouve e preenche `naturalidade` e `clareza` (inteiros de 1 a 5). Depois:

```bash
python testes/avaliar_tts.py resumir
```

**Avaliação por nota geral (a que o grupo usou).** O grupo avaliou os áudios de `tts_cego` com 6 pessoas em 3 duplas e deu **uma nota geral** por áudio, de 1 a 10, o que não permite separar naturalidade de clareza. Para esse caso, `python testes/tts_notas_gerais.py --importar "<60 números: 3 por áudio, na ordem aval_01 a aval_20>"` guarda as notas em `testes/tts_cego_notas_gerais.csv`, converte para 1 a 5 (`1 + (nota - 1) * 4 / 9`), junta com a chave cega e grava `evidencias/tts_notas.csv` e `evidencias/tts_resumo.md`. O fluxo abaixo, com as duas notas separadas, é o que o enunciado pede e continua disponível.

**Avaliação cega (recomendada).** O nome do arquivo em `audios_teste/tts/` revela o motor. Para os avaliadores não saberem qual estão ouvindo, use `python testes/tts_cego.py preparar`: ele embaralha os 20 áudios em `audios_teste/tts_cego/aval_01.wav...` (todos WAV mono 22,05 kHz) e cria `testes/tts_cego_notas.csv` para as notas. Cada avaliador ouve os 20 áudios na ordem de `aval_01` a `aval_20` e preenche `naturalidade` e `clareza` (1 a 5); troque "Avaliador 1, 2 e 3" pelos nomes. Depois: `python testes/tts_cego.py consolidar` (passa as notas para `planilha_tts.csv`, recusa nota fora de 1 a 5 e menos de 3 pessoas) e `python testes/avaliar_tts.py resumir`. Não mostre `testes/tts_cego_chave.csv` aos avaliadores antes do fim. No relatório, registre que a avaliação foi cega.

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
