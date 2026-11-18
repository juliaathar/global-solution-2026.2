# LLM: resultados

| Modelo | Perguntas | % corretas (normal+cont.) | % normais | % continuação | % recusas adequadas (fora do escopo) | % abstenção (sem dado) | Latência média por chamada ao LLM (s) |
|---|---|---|---|---|---|---|---|
| ollama/qwen2.5:3b | 30 | 91.3% | 94.4% | 80.0% | 100.0% | 100.0% | 8.03 |
| ollama/qwen2.5:1.5b | 30 | 60.9% | 66.7% | 40.0% | 100.0% | 50.0% | 6.22 |

## Erros para análise

| Modelo | Id | Tipo | Pergunta | Resposta |
|---|---|---|---|---|
| ollama/qwen2.5:3b | q08 | continuacao | E o que eu levo? | Leve seu documento de identificação atual, que é o RG. |
| ollama/qwen2.5:3b | q17 | normal | Posso usar certidão de casamento para tirar a segunda via do RG? | Não, certidão de casamento não serve para tirar segunda via do RG. Leve certidão de nascimento ou casamento e comprovante de residência. |
| ollama/qwen2.5:1.5b | q04 | continuacao | E que horas ela fecha? | A UBS fecha às dezesseis horas, de segunda a sexta. |
| ollama/qwen2.5:1.5b | q08 | continuacao | E o que eu levo? | Leve documento com foto e cartão do SUS. |
| ollama/qwen2.5:1.5b | q09 | normal | Tem um buraco na minha rua. Como eu aviso? | 1. Primeiro, marque o buraco com um sinal indicador.
2. Em seguida, avise a administração local ou a UBS.
3. Se possível, envie fotos para a UBS. |
| ollama/qwen2.5:1.5b | q10 | continuacao | E isso gera algum número para acompanhar? | Não, não gera número específico. |
| ollama/qwen2.5:1.5b | q13 | normal | Onde posso fazer o Cadastro Único? | No centro da cidade. |
| ollama/qwen2.5:1.5b | q17 | normal | Posso usar certidão de casamento para tirar a segunda via do RG? | Não, a certidão de casamento não é necessária para tirar a segunda via do RG. Você precisa levar a certidão de nascimento ou casamento, comprovante de residênci |
| ollama/qwen2.5:1.5b | q18 | normal | O poste da minha rua está apagado. O que eu faço? | Primeiro, você precisa verificar se o poste está realmente apagado. Se sim, pode ser que seja necessário um serviço de manutenção. Ligue para a Defesa Civil ou  |
| ollama/qwen2.5:1.5b | q19 | normal | Como relato lixo acumulado na calçada? | Peço para limpar a calçada. |
| ollama/qwen2.5:1.5b | q22 | normal | Onde faço a segunda via de identidade? | Leve certidão de nascimento ou casamento e comprovante de residência. |
| ollama/qwen2.5:1.5b | q30 | sem_resposta | Quanto custa a segunda via do RG? | Para obter a segunda via do RG, você precisa levar a certidão de nascimento ou casamento e o comprovante de residência. Não há custo para isso. |