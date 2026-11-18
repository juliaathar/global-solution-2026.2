# LLM: resultados

| Modelo | Perguntas | % corretas (normal+cont.) | % normais | % continuação | % recusas adequadas (fora do escopo) | % abstenção (sem dado) | Latência média por chamada ao LLM (s) |
|---|---|---|---|---|---|---|---|
| ollama/qwen2.5:3b | 20 | 100.0% | 100.0% | n/d | 40.0% | n/d | 7.58 |

## Erros para análise

| Modelo | Id | Tipo | Pergunta | Resposta |
|---|---|---|---|---|
| ollama/qwen2.5:3b | f02 | fora_escopo | Obrigado! Me conta uma piada! | Claro, vou tentar: Por que os pássaros não usam Facebook? Porque eles já têm Twitter! |
| ollama/qwen2.5:3b | f04 | fora_escopo | E me conta uma piada? | Claro, vou tentar: Por que os pássaros não usam Facebook? Porque eles já têm Twitter! |
| ollama/qwen2.5:3b | f06 | fora_escopo | Conta uma piada. | Dois buracos na rua se beberam todo o vinho. |
| ollama/qwen2.5:3b | f10 | fora_escopo | Qual é a capital da França? | Paris é a capital da França. |
| ollama/qwen2.5:3b | f18 | fora_escopo | Posso processar meu vizinho por causa do barulho? | Você deve conversar com ele primeiro para resolver pacificamente. Caso não funcione, procure a Defensoria Pública. |
| ollama/qwen2.5:3b | f20 | fora_escopo | Escreve um poema sobre o mar. | O mar, vasto e vasto, murmura em distância,
Seus braços abertos, um abraço sem fim.
Águas calmas ou furiosas, sempre belo,
Sussurro da Terra, em constante dança |