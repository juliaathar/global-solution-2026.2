# Parâmetros da simulação (iSPD)

Projeto: **EloBairro**. Disciplina: Cluster Computing.

> **Todos os valores abaixo são hipóteses do modelo, não medições.** A simulação não representa um cluster real. Unidades de tamanho computacional (MFLOPS) e comunicação (Mbits) confirmadas na interface do iSPD. Banda e latência não exibem unidade na interface; adotados Mbits/s e s, coerentes com o tempo de comunicação de 0,042 s por tarefa obtido na simulação.

## Tarefa simulada

Classificar fotos de fissuras e danos em lote (módulo `04-visao-computacional`) em um dia de pico, como depois de uma chuva forte, quando muitos cidadãos enviam fotos ao mesmo tempo.

## Carga (idêntica nos dois cenários)

| Parâmetro | Valor | Unidade | Origem |
|---|---|---|---|
| Número de tarefas | 1000 | imagens | hipótese: pico de um dia |
| Tamanho computacional por tarefa | 2000 | MFlops | hipótese: inferência de um classificador de imagens |
| Comunicação de ida por tarefa | 4 | Mbits | hipótese: foto de cerca de 500 KB enviada ao worker |
| Comunicação de volta por tarefa | não modelada | - | retorno do rótulo desconsiderado |
| Chegada das tarefas | todas em t = 0 | - | lote único |

Configuração no iSPD (carga Random): mínimo = médio = máximo para tamanho fixo; Probability = 0.

## Infraestrutura (idêntica nos dois cenários, exceto o nº de workers)

| Parâmetro | Cenário A | Cenário B | Unidade |
|---|---|---|---|
| Workers | **2** | **4** | máquinas |
| Capacidade por worker | 1000 | 1000 | MFlops/s |
| Núcleos (Cores) por worker | 1 | 1 | núcleos |
| Mestre | 1 (no próprio cluster) | 1 (no próprio cluster) | máquina |
| Banda de cada link | 100 | 100 | Mbits/s |
| Latência de cada link | 0,001 | 0,001 | s |
| Escalonador | Workqueue | Workqueue | - |

Escalonador: Workqueue (opções da versão usada: Workqueue, RoundRobin e DynamicFPLTF). Bandwidth e Latency são definidos no próprio cluster.

## Valores esperados (só para conferir o resultado)

- Tempo de cálculo por tarefa: 2000 / 1000 = 2 s.
- Cenário A: 1000 × 2 s / 2 workers = cerca de 1000 s.
- Cenário B: 1000 × 2 s / 4 workers = cerca de 500 s.
- Transferência por tarefa: 4 Mbits / 100 Mbits/s = 0,04 s. Como o mestre envia tudo pelo mesmo link, o envio das 1000 imagens leva cerca de 40 s e pode virar gargalo no cenário B.
- Razão ideal T2/T4 = 2.

Se o iSPD mostrar tempos diferentes, o relatório deve explicar a diferença (rede, mestre, escalonador, distribuição).

## Regra de comparação

Só a quantidade de workers muda entre A e B. Carga, capacidade, escalonador, banda e latência ficam iguais.

## Se quiser aproximar do real

Substituir o tamanho computacional pela latência de inferência medida em `04-visao-computacional` e declarar a origem aqui.
