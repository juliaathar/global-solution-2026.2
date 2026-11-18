# LLM: resultados

| Modelo | Perguntas | % corretas (normal+cont.) | % normais | % continuação | % recusas adequadas (fora do escopo) | % abstenção (sem dado) | Latência média por chamada ao LLM (s) |
|---|---|---|---|---|---|---|---|
| ollama/qwen2.5:3b | 30 | 82.6% | 83.3% | 80.0% | 100.0% | 100.0% | 6.46 |

## Erros para análise

| Modelo | Id | Tipo | Pergunta | Resposta |
|---|---|---|---|---|
| ollama/qwen2.5:3b | q08 | continuacao | E o que eu levo? | Leve seu documento de identificação atual (RG) e o cartão do SUS. |
| ollama/qwen2.5:3b | q14 | normal | O CRAS pede comprovante de residência? | Não, o CRAS pede certidão de nascimento ou casamento e comprovante de residência. |
| ollama/qwen2.5:3b | q17 | normal | Posso usar certidão de casamento para tirar a segunda via do RG? | Não, certidão de casamento não serve para tirar segunda via do RG. Leve certidão de nascimento. |
| ollama/qwen2.5:3b | q18 | normal | O poste da minha rua está apagado. O que eu faço? | Ligue para a empresa responsável por manutenção de postes ou procure a Companhia de Água e Esgoto. |