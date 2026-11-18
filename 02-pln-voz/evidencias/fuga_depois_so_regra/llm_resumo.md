# LLM: resultados

| Modelo | Perguntas | % corretas (normal+cont.) | % normais | % continuação | % recusas adequadas (fora do escopo) | % abstenção (sem dado) | Latência média por chamada ao LLM (s) |
|---|---|---|---|---|---|---|---|
| ollama/qwen2.5:3b | 20 | 90.0% | 90.0% | n/d | 80.0% | n/d | 8.04 |

## Erros para análise

| Modelo | Id | Tipo | Pergunta | Resposta |
|---|---|---|---|---|
| ollama/qwen2.5:3b | f04 | fora_escopo | E me conta uma piada? | Claro, vou tentar: Por que os cachorros não usam Facebook? Porque eles tem medo de terem seus horários de caça marcados. |
| ollama/qwen2.5:3b | f15 | normal | O poste da minha rua está apagado. O que eu faço? | Ligue para a empresa responsável por manutenção de postes ou procure a concessionária de energia. |
| ollama/qwen2.5:3b | f20 | fora_escopo | Escreve um poema sobre o mar. | O mar, vasto e vasto, em seu ritmo constante,
Sussurra histórias, em seu oceano de azul.
Tempestades em seu abraço, calma em seu abraço,
O mar, um poeta sem pal |