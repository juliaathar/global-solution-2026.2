# LLM: resultados

| Modelo | Perguntas | % corretas (normal+cont.) | % normais | % continuação | % recusas adequadas (fora do escopo) | % abstenção (sem dado) | Latência média por chamada ao LLM (s) |
|---|---|---|---|---|---|---|---|
| ollama/qwen2.5:3b | 30 | 82.6% | 83.3% | 80.0% | 100.0% | 100.0% | 55.39 |
| ollama/qwen2.5:1.5b | 30 | 82.6% | 83.3% | 80.0% | 100.0% | 100.0% | 29.71 |

## Erros para análise

| Modelo | Id | Tipo | Pergunta | Resposta |
|---|---|---|---|---|
| ollama/qwen2.5:3b | q10 | continuacao | E quais ficam no Centro? | Ecoponto Sítio Bom Jesus: R. Hilário Santana, 5 - Parque Res. Flamboyant
Ecoponto Florianópolis: Av. Mal. Floriano Peixoto, 154 - Centro |
| ollama/qwen2.5:3b | q19 | normal | Quantas UBS existem na cidade? | Existem 16 UBSs na cidade. |
| ollama/qwen2.5:3b | q20 | normal | Dá para tomar vacina na UBS até a hora de fechar? | Sim, a vacinação é encerrada uma hora antes do fechamento das unidades. |
| ollama/qwen2.5:3b | q21 | normal | Como peço para tirar uma árvore que oferece risco? | Não tenho essa informação com segurança. Posso ajudar com serviços públicos do bairro, como UBS, CRAS e documentos. Para saúde, assuntos jurídicos ou emergência |
| ollama/qwen2.5:1.5b | q10 | continuacao | E quais ficam no Centro? | No Centro da cidade, os ecopontos estão localizados em:

1. R. Hilário Santana, 5 - Parque Res. Flamboyant
2. R. Setenta, 54 - Vila Progresso
3. R. do Cruzeiro, |
| ollama/qwen2.5:1.5b | q11 | normal | Quem tem direito ao leite gratuito para crianças? | As crianças de baixa renda que estão na faixa etária de 6 meses a 5 anos e 11 meses de idade, e que vivem em situação de risco nutricional, têm direito ao leite |
| ollama/qwen2.5:1.5b | q19 | normal | Quantas UBS existem na cidade? | Existem 14 Unidades Básicas de Saúde (UBS) na cidade. |
| ollama/qwen2.5:1.5b | q21 | normal | Como peço para tirar uma árvore que oferece risco? | Não tenho essa informação com segurança. Posso ajudar com serviços públicos do bairro, como UBS, CRAS e documentos. Para saúde, assuntos jurídicos ou emergência |