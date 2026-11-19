# LLM: resultados

| Modelo | Perguntas | % corretas (normal+cont.) | % normais | % continuação | % recusas adequadas (fora do escopo) | % abstenção (sem dado) | Latência média por chamada ao LLM (s) |
|---|---|---|---|---|---|---|---|
| ollama/qwen2.5:3b | 30 | 73.9% | 77.8% | 60.0% | 100.0% | 100.0% | 57.76 |

## Erros para análise

| Modelo | Id | Tipo | Pergunta | Resposta |
|---|---|---|---|---|
| ollama/qwen2.5:3b | q02 | continuacao | E onde eu faço isso? | Não tenho essa informação com segurança. Posso ajudar com serviços públicos do bairro, como UBS, CRAS e documentos. Para saúde, assuntos jurídicos ou emergência |
| ollama/qwen2.5:3b | q10 | continuacao | E quais ficam no Centro? | ECOPONTO SÍTIO BOM JESUS - R. Hilário Santana, 5 - Parque Res. Flamboyant
ECOPONTO FLORIANO PEIXOTO - Av. Mal. Floriano Peixoto, 154 - Centro |
| ollama/qwen2.5:3b | q19 | normal | Quantas UBS existem na cidade? | Existem 12 UBSs na cidade. |
| ollama/qwen2.5:3b | q20 | normal | Dá para tomar vacina na UBS até a hora de fechar? | Sim, a vacinação é encerrada uma hora antes do fechamento das unidades. |
| ollama/qwen2.5:3b | q21 | normal | Como peço para tirar uma árvore que oferece risco? | Não tenho essa informação com segurança. Posso ajudar com serviços públicos do bairro, como UBS, CRAS e documentos. Para saúde, assuntos jurídicos ou emergência |
| ollama/qwen2.5:3b | q22 | normal | Quem é atendido pelo Integra? | Até 14 anos. Para pessoas com deficiência acima de 14 anos. |