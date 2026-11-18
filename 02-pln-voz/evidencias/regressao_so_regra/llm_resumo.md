# LLM: resultados

| Modelo | Perguntas | % corretas (normal+cont.) | % normais | % continuação | % recusas adequadas (fora do escopo) | % abstenção (sem dado) | Latência média por chamada ao LLM (s) |
|---|---|---|---|---|---|---|---|
| ollama/qwen2.5:3b | 30 | 87.0% | 88.9% | 80.0% | 100.0% | 100.0% | 6.58 |

## Erros para análise

| Modelo | Id | Tipo | Pergunta | Resposta |
|---|---|---|---|---|
| ollama/qwen2.5:3b | q08 | continuacao | E o que eu levo? | Leve documento com foto e cartão do SUS. |
| ollama/qwen2.5:3b | q17 | normal | Posso usar certidão de casamento para tirar a segunda via do RG? | Não sei essa informação. Pergunte em uma secretaria de identidade. |
| ollama/qwen2.5:3b | q18 | normal | O poste da minha rua está apagado. O que eu faço? | Ligue para a empresa responsável por manutenção de postes ou procure a Companhia de Água e Esgoto. |