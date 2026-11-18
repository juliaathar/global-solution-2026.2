# Análise: geração e sistema completo (49 perguntas)

Números em `sistema_completo_resumo.md`; respostas, contextos recuperados e julgamentos em `sistema_completo.json` e `sistema_completo.csv`. Reproduzir: `python avaliacao/avaliar_sistema.py` (usa a API da OpenAI; custo de centavos).

Configuração: chunking por seção, e5-large, top-3, limiar de cosseno 0,84, `gpt-4o-mini`, temperatura 0,1, 400 tokens.

## Resultados
| Nível | Resultado |
|---|---|
| Sistema completo, respondíveis (30) | 28 corretas, 1 parcial, 1 falsa abstenção (V04, "O que o PAIF faz?") |
| Sistema completo, continuações (5 de 30 acima) | 4 de 5 corretas segundo o juiz; a 5ª (C02) é erro do juiz, ver abaixo |
| Sem resposta (10) | 10 de 10 se abstiveram |
| Desvio de propósito (5) | 5 de 5 recusadas ou abstidas (D01 bloqueada pelo filtro de entrada, o resto pela abstenção) |
| Ambíguas (4) | 3 de 4; A01 ("Quero fazer o cadastro") foi respondida como Cadastro Único sem pedir esclarecimento |
| Geração com trecho correto (30) | 29 corretas, 30 fundamentadas, 29 citam a fonte |
| Abstenção só pelo prompt, limiar desligado (18) | 16 de 18 se abstiveram; sem resposta 10/10, desvio 4/4, ambíguas 2/4 |

## Leitura crítica
**O pipeline funciona bem neste conjunto, mas o conjunto é fácil e pequeno.** As perguntas respondíveis foram escritas a partir de trechos do próprio corpus e a maioria tem a resposta em uma única página. Os números mostram que o sistema funciona nesse cenário, e não que ele generaliza para perguntas reais de cidadãos (mais vagas, com gíria e erros de digitação). Com 30 respondíveis, um erro vale 3 pontos percentuais.

**O juiz é a parte menos confiável da medição.**
- O juiz configurado era o `gpt-4o`, mas a chave não teve acesso e o script recorreu ao `gpt-4o-mini`, o mesmo modelo que gera as respostas. Um modelo avaliando a si mesmo tende a ser benevolente.
- Mesmo assim, o juiz errou em duas direções. Em **C02**, marcou como "não sustentada" a exigência de NIS e renda per capita, mas esses itens estão na página de transporte adaptado ("Número da Inscrição Social (NIS) e renda per capita"). A resposta estava fundamentada; o erro foi do juiz, que comparou com a resposta de referência em vez dos trechos. Em **R12** (contexto controlado), marcou "parcial" por a resposta listar também a UES 3, que consta no trecho.
- Conclusão: as taxas "fundamentada 97%" e "parcial" devem ser lidas como estimativa. Verificadas a mão, as 2 marcações de "não sustentada" ou "parcial" estavam erradas, o que sugere que a fundamentação real nas respondidas é 29/29 neste conjunto. Isso ainda precisa de revisão humana de uma amostra (coluna `julgamento_humano` do CSV) para entrar no relatório.

**Abstenção em camadas funciona, mas não por margem larga.**
- O limiar (0,84) e a regra do prompt, cada um sozinho, seguram quase tudo: sem resposta 10/10 nos dois casos, desvio 4/4 sem limiar.
- Onde cada camada falha é diferente: o prompt sozinho deixou passar as ambíguas A01 e A02 (respondeu usando o primeiro assunto que encontrou: telefone de manutenção e de lixeiras, sem saber de quê o usuário falava); o limiar sozinho recusou V04 (respondível, cosseno 0,835). Manter as duas é o que dá 100% nas sem resposta.
- Essas 18 perguntas de abstenção não incluem tentativas adversariais elaboradas. Isso é o próximo passo.

**Ambiguidade é resolvida por abstenção, não por esclarecimento.** "Qual o telefone?", "Como faço para reclamar?" e "Preciso de ajuda" receberam "não encontrei essa informação". Para o público do EloBairro, uma pergunta de volta ("De qual serviço você precisa o telefone?") ajudaria mais. A01 mostra o risco oposto: respondeu com o Cadastro Único, que provavelmente era o que se queria, mas sem confirmar.

**Respostas longas:** 5 das 29 respondidas (R01, R02, R09, R12, C02) passam de 4 frases (de 6 a 12 "frases", contando itens de lista). Em R01 e R09 a resposta é uma lista de documentos ou endereços, o que é razoável, mas contraria a regra do prompt. Para a voz (02), listas longas são ruins; a adaptação para fala deve resumir.

**Limites de uso para o cidadão:** o assistente não conhece o conteúdo dos PDFs (editais, listas de documentos) e várias páginas são índices. Quando a página não traz a resposta, ele se abstém e manda ligar para o 156, o que é seguro mas pode frustrar quem já está sem saber onde ir. A página de tapa-buracos só tem a programação semanal; perguntas sobre como pedir o serviço dependem de o 156 estar em outro trecho.

## O que falta
1. Testes adversariais (prompt injection direto e indireto, vazamento de prompt/dados, instruções maliciosas dentro de documentos): obrigatório no enunciado, só há o filtro de entrada e a neutralização de contexto implementados, sem avaliação.
2. Revisão humana de amostra e, se possível, juiz de modelo diferente do generator.
3. Perguntas de pessoas de fora do grupo (3 pessoas já são exigidas pela disciplina de front-end) para testar generalização.
4. Ajustes de prompt (esclarecimento para ambíguas, limite de frases), medindo antes e depois.
