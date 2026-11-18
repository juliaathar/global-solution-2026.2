# Sistema completo e geração (juiz: gpt-4o-mini, generator: gpt-4o-mini)

## A. Sistema completo, perguntas respondíveis e continuações

| Métrica | Resultado |
|---|---|
| Perguntas | 30 |
| Falsa abstenção (recusou pergunta respondível) | 1/30 (3%) |
| Correta (sim) entre as respondidas | 28/29 (97%) |
| Parcial | 1/29 (3%) |
| Fundamentada (sem afirmação fora dos trechos) | 28/29 (97%) |
| Taxa de resposta não sustentada | 1/29 (3%) |
| Cita a fonte [n] | 29/29 (100%) |
| Mais de 4 frases (regra do prompt) | 5/29 (17%) |
| Correta de ponta a ponta (sobre todas as 30) | 28/30 (93%) |
| Continuação correta (consistência entre turnos) | 4/5 (80%) |

## A. Sistema completo, perguntas sem evidência

| Tipo | Perguntas | Comportamento esperado atendido |
|---|---|---|
| sem_resposta | 10 | 10/10 (100%) |
| desvio | 5 | 5/5 (100%) |
| ambigua | 4 | 3/4 (75%) |

Ambíguas contam como atendidas se o sistema se absteve ou fez pergunta de esclarecimento (regra simples: resposta com '?'); revisar a mão.

## B. Geração com contexto controlado (trecho correto fornecido)

| Métrica | Resultado |
|---|---|
| Perguntas | 30 |
| Correta (sim) | 29/30 (97%) |
| Parcial | 1/30 (3%) |
| Fundamentada | 30/30 (100%) |
| Cita a fonte [n] | 29/30 (97%) |
| Mais de 4 frases | 4/30 (13%) |

## C. Abstenção só pela regra do prompt (limiar desativado)

| Tipo | Perguntas | LLM se absteve ou recusou |
|---|---|---|
| sem_resposta | 10 | 10/10 (100%) |
| desvio | 4 | 4/4 (100%) |
| ambigua | 4 | 2/4 (50%) |
| total | 18 | 16/18 (89%) |

## Falhas (para a análise)

- **R12** Qual o horário das Unidades de Especialidade de Saúde? — B correta=parcial
- **A01** Quero fazer o cadastro — C: LLM respondeu sem evidência
- **A02** Qual o telefone? — C: LLM respondeu sem evidência
- **C02** E quais documentos eu preciso? — correta=parcial; não sustentada: Número da Inscrição Social (NIS) e renda per capita não são mencionados na resposta de referência como documentos necess
- **V04** O que o PAIF faz? — falsa abstenção