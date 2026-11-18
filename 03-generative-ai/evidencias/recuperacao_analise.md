# Análise da recuperação (BM25, 21 perguntas com evidência, 5 sem resposta)

Números em `recuperacao_resumo.md`; detalhe por pergunta em `recuperacao_detalhe.csv`. Conjunto de perguntas em `../avaliacao/perguntas.json`.

## Chunking
- `tam800_ov120` foi o melhor: evidência no top-1 em 71% das perguntas (MRR 0,75), contra 38% de `tam300_ov0` e 48% de `secao`.
- Trechos de 300 caracteres separam a resposta do cabeçalho do serviço (endereço numa linha, horário na seguinte) e perdem contexto. O acerto de documento no top-3 é igual nas três (0,90), então o que muda é achar o trecho certo dentro do documento.
- Por seção funciona no top-3 (0,81), mas as seções do portal são desiguais: títulos de cartão sem corpo e blocos grandes de endereços.
- Limitação: 21 perguntas escritas pelo grupo. Diferenças de 1 a 2 perguntas (5 a 10 pontos percentuais) não são conclusivas.

## Erros de recuperação (tam800_ov120)
| Pergunta | O que houve | Causa provável |
|---|---|---|
| R11 remover árvore com risco | nenhum trecho do documento certo no top-5 | vocabulário diferente: a página diz "supressão", a pergunta diz "remover" |
| R14 colocar lixeira na rua | idem; top-1 foi a página de varrição | página diz "implantação"/"reposição" de lixeiras; "colocação" não casa |
| R13 quantas UBS | documento certo no top-1, mas o trecho com "40 UBSs" não foi recuperado | "UBS" na pergunta e "UBSs" no texto viram tokens diferentes |
| R15 o que é o CRAS | documento certo no top-1, trecho com a definição fora do top-5 | a página repete "Cras" em muitos trechos de endereço |
| R16, C04 | evidência só na 3ª posição | termos genéricos ("atendido", "idade") casam com outras páginas |

Todos são falhas lexicais (sinônimo, plural, termo genérico). É o argumento para testar recuperação vetorial e híbrida na próxima etapa.

## Abstenção por pontuação
O score relativo do melhor trecho **não separa** pergunta respondível de pergunta sem resposta:
- As 5 perguntas sem resposta têm top-1 entre 0,34 e 0,64 (S05, "previsão do tempo", chega a 0,64 em "Vacinação" por causa de "tempo de espera").
- Com limiar 0,50 em `tam800_ov120`, só 20% das perguntas sem resposta passam, mas 33% das respondíveis são recusadas.
- Com limiar 0,25 (valor atual), 100% das sem resposta passam e 5% das respondíveis são recusadas.
- Ou seja, só o limiar de BM25 não basta como proteção contra resposta não sustentada. A abstenção precisa também de outro sinal: regra do LLM no prompt (já existe, ainda não avaliada), score de recuperação densa ou verificação de que os termos da pergunta aparecem no trecho.

## Alterações no corpus descobertas nesta etapa
- A página `cartao-de-estacionamento-do-idoso` trazia só termos de uso do portal e foi removida do corpus. Isso explicava a abstenção da pergunta correspondente no teste rápido anterior: nesse caso a abstenção estava certa, e o erro estava na fonte.
- O limiar de 0,25 não foi alterado. Ele só será calibrado depois de comparar os retrievers, para não ajustar sobre o mesmo conjunto que avalia.
