# Validação do limiar (chunking por seção + e5-large)

Desenvolvimento: 21 respondíveis e 9 sem evidência. Validação (perguntas novas): 9 respondíveis e 8 sem evidência.

- Limiar de borda (máx. 1-FA-FR no desenvolvimento): **0.844** (FA 0.00, FR 0.00)
- Menor sinal respondível no desenvolvimento: 0.844; maior sinal sem evidência: 0.834
- Limiar do ponto médio da margem: **0.839**

Recuperação na validação: evidência no top-1 em 5/9, no top-3 em 8.

| Limiar | Falsa abstenção | Falsa resposta |
|---|---|---|
| 0.844 (borda) | 0.11 (1/9) | 0.00 (0/8) |
| 0.839 (ponto médio) | 0.11 (1/9) | 0.00 (0/8) |

## Detalhe da validação

| Id | Pergunta | Pos. evidência | Cosseno top-1 | Documento top-1 |
|---|---|---|---|---|
| V01 | Quem pode participar da Casa do Idoso? | 2 | 0.874 | apoio-social-ao-cidadao-casa-do-idoso |
| V02 | Quem tem direito ao benefício eventual? | 2 | 0.884 | apoio-social-ao-cidadao-beneficios-eventuais |
| V03 | Posso levar entulho de uma pequena reforma da minha casa a algum lugar? | 5 | 0.850 | manutencao-da-cidade-pevs-na-cidade |
| V04 | O que o PAIF faz? | 1 | 0.835 | apoio-social-ao-cidadao-cras |
| V05 | Idoso tem passagem de ônibus de graça? | 1 | 0.877 | mobilidade-urbana-beneficios-para-idosos-e-pcd |
| V06 | Dá para tomar vacina na UBS até a hora de fechar? | 1 | 0.864 | saude-unidades-basicas-de-saude-ubs-unidades-basicas-de-saude |
| V07 | Qual o objetivo da Lei da Calçada? | 1 | 0.855 | mobilidade-urbana-calcada-segura |
| V08 | Qual o telefone do serviço de controle de pragas? | 1 | 0.873 | manutencao-da-cidade-controle-de-pragas |
| V09 | E onde faço a inscrição? | 2 | 0.876 | apoio-social-ao-cidadao-casa-do-idoso |
| V10 | Como faço a matrícula do meu filho na escola municipal? | - | 0.824 | apoio-social-ao-cidadao-beneficios-eventuais |
| V11 | Como me inscrever no Minha Casa Minha Vida? | - | 0.820 | apoio-social-ao-cidadao-casa-do-idoso |
| V12 | Quais os horários do ônibus da linha 066? | - | 0.818 | mobilidade-urbana-transporte-adaptado |
| V13 | Como abrir uma empresa de microempreendedor individual na cidade? | - | 0.822 | mobilidade-urbana-transporte-adaptado |
| V14 | Qual o valor do auxílio-reclusão? | - | 0.834 | apoio-social-ao-cidadao-beneficios-eventuais |
| V15 | Você pode me ajudar com a minha lição de matemática? | - | 0.810 | saude-saude-mental |
| V16 | Quem ganhou o jogo do Corinthians ontem? | - | 0.784 | manutencao-da-cidade-pevs-na-cidade |
| V17 | Preciso de ajuda | - | 0.820 | apoio-social-ao-cidadao-cadastro-unico |

Latência média por consulta (embedding da pergunta + busca, CPU): 103 ms.