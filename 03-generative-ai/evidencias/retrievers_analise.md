# Análise: BM25 x vetorial x híbrido

Tabela completa em `retrievers_resumo.md`; por pergunta em `retrievers_detalhe.csv`. Reproduzir: `python avaliacao/avaliar_retrievers.py`.

Modelos de embedding (via fastembed, ONNX, CPU):
- `minilm` = paraphrase-multilingual-MiniLM-L12-v2 (384 dim, entrada de até 128 tokens).
- `e5large` = intfloat/multilingual-e5-large (1024 dim, entrada de até 512 tokens, com prefixos query/passage).
- Híbrido = Reciprocal Rank Fusion (k=60) entre BM25 e o vetorial, 20 candidatos de cada.

## Recuperação (21 perguntas com evidência)
| Melhor por retriever | Chunking | Evid@1 | Evid@3 | MRR |
|---|---|---|---|---|
| BM25 | tam800_ov120 | 0,71 | 0,81 | 0,75 |
| Vetorial MiniLM | secao / tam300 | 0,57 / 0,43 | 0,71 / 0,62 | 0,65 / 0,56 |
| Híbrido MiniLM | tam800_ov120 | 0,76 | 0,86 | 0,81 |
| **Vetorial e5-large** | **secao** | **0,95** | **1,00** | **0,98** |
| Híbrido e5-large | tam800_ov120 | 0,76 | 0,90 | 0,84 |

- O melhor conjunto medido foi **chunking por seção + vetorial e5-large**: evidência no top-1 em 20 de 21 perguntas e no top-3 em todas.
- O MiniLM só olha os primeiros 128 tokens de cada trecho, então perde o final de trechos de 800 caracteres e de seções. Isso explica por que ele fica abaixo do BM25 em `secao` e `tam800` no top-1, mas ajuda como complemento no híbrido (MRR 0,81 contra 0,75 do BM25 sozinho).
- O e5-large aceita 512 tokens e se beneficia dos trechos maiores. Com ele, as falhas lexicais da análise anterior (remover árvore, colocar lixeira, UBS/UBSs) desaparecem.
- O híbrido não superou o vetorial puro com e5-large. A fusão por RRF dá o mesmo peso ao BM25, que aqui é o ranking mais fraco, e arrasta bons resultados para baixo (0,95 para 0,71 em `secao`). Um peso menor para o BM25 ou um reranker poderia mudar isso; não foi testado.

## Sinal para abstenção
- Com BM25, o score do melhor trecho quase não separa perguntas respondíveis das sem evidência (AUC 0,54 a 0,59, perto do acaso). Já tinha aparecido na análise anterior.
- Com o cosseno do e5-large a separação é quase perfeita (AUC 0,99 a 1,00). Com o MiniLM, 0,85 a 0,89.
- No melhor ponto, o e5-large com `secao` recusa nenhuma pergunta respondível (FA 0,00) e deixa passar nenhuma sem evidência (FR 0,00), com limiar de cosseno 0,84.

## Cuidados antes de adotar esses números
- 30 perguntas, escritas pelo próprio grupo e depois usadas para escolher o limiar: FA e FR de 0,00 são otimistas. O limiar (0,84) foi escolhido no mesmo conjunto que o avalia.
- O cosseno do e5 fica numa faixa comprimida (aqui, limiar ~0,84), então a margem entre respondível e não respondível pode ser estreita. Antes de fixar o valor, validar com perguntas novas (ideal: 10 a 15 novas, incluindo sem resposta próximas do tema, como "como pedir poda de árvore em casa particular").
- O e5-large pesa cerca de 2,2 GB e é mais lento que o BM25 (a indexação de 125 trechos e cada consulta rodam em CPU). Para a demo ao vivo e a voz, medir a latência da consulta.
- As perguntas sem evidência foram escritas sem consultar o corpus em detalhe; algumas podem ter resposta parcial no portal (por exemplo, "segunda via de certidão" e "IPTU"), o que deve ser conferido nas falhas.

## Validação em perguntas novas (`validacao_limiar.md`)
17 perguntas escritas depois da escolha de chunking, modelo e limiar (9 respondíveis, 8 sem evidência), sem reajuste.

- **Recuperação caiu bastante fora do conjunto de desenvolvimento:** evidência no top-1 em 5 de 9 (0,56) e no top-3 em 8 de 9, contra 0,95 e 1,00 antes. Os 0,95 eram otimistas, como se previa. A diferença vem em parte do tamanho dos conjuntos (9 perguntas: um erro vale 11 pontos) e em parte de perguntas mais coloquiais ("entulho de pequena reforma" em vez de "PEV").
- **Abstenção, limiar 0,84:** nenhuma das 8 sem evidência passou (FR 0/8) e 1 respondível foi recusada (V04 "O que o PAIF faz?", cosseno 0,835), ou seja, FA 1/9.
- **A margem é estreita:** no desenvolvimento, o menor sinal respondível é 0,844 e o maior sem evidência é 0,834 (diferença de 0,01). Na validação, V04 (respondível) está em 0,835 e V14 (sem evidência) em 0,834. Um limiar de cosseno do e5 é um sinal frágil sozinho. O resultado "FA e FR em 0,00" do desenvolvimento não vale como estimativa de desempenho real.
- **Conclusão para o motor:** manter 0,84 como limiar da primeira barreira, mas tratar a abstenção como defesa em camadas: (1) cosseno, (2) regra de abstenção no prompt do LLM, (3) verificação da resposta contra os trechos na avaliação do sistema completo. Perguntas sem resposta próximas do tema (V10 a V14, 0,82 a 0,83) é onde o limiar mais corre risco.
- **Latência:** cerca de 100 ms por consulta em CPU e 5 s para carregar o modelo na primeira chamada.

## Estado do motor
`rag/motor.py` agora usa chunking por seção + e5-large + limiar 0,84. O teste rápido manteve a abstenção correta em "passaporte" e "bitcoin" e a recuperação certa em Cadastro Único e na continuação sobre o CREAS. A pergunta sobre tapa-buracos continua se abstendo (cosseno 0,821): a página só traz a programação semanal de ruas, sem explicar o serviço, então a abstenção reflete uma lacuna do corpus.
