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

## Comparação com a medição da `04-visao-computacional`

O classificador simulado é a MobileNetV2 da disciplina de Visão Computacional, com entrada de 224×224. Ela custa cerca de 300 milhões de multiplicações-somas por imagem, ou seja, cerca de **600 MFLOPS**. Num notebook com CPU Intel i5-6300U, a latência medida foi de cerca de **60 ms por imagem** (`04-visao-computacional/evidencias/benchmark.txt`).

A hipótese de 2000 MFLOPS por tarefa é, portanto, cerca de 3 vezes o custo do modelo, e os workers de 1000 MFLOPS/s são mais lentos que o notebook usado na 04. As duas escolhas são conservadoras: equivalem a um modelo mais pesado ou a máquinas mais modestas. Elas não mudam a conclusão da comparação, mas mudam o ponto em que a rede vira gargalo.

Estimativa com o custo do modelo (calculada, **não simulada** no iSPD; mesmos 1000 tarefas, rede e escalonador):

| | Hipótese simulada | Com 600 MFLOPS por imagem |
|---|---|---|
| Cálculo por tarefa (worker de 1000 MFLOPS/s) | 2 s | 0,6 s |
| Comunicação por tarefa | 0,042 s (2 % do cálculo) | 0,042 s (7 % do cálculo) |
| T2 estimado | 1021 s (simulado) | cerca de 500 × 0,642 = 321 s |
| T4 estimado | 511 s (simulado) | cerca de 250 × 0,642 = 160 s |
| Razão T2/T4 | 2,00 | cerca de 2,0 |
| Workers a partir dos quais a comunicação do mestre (42 s) limita | cerca de 48 | cerca de 14 |

Leitura: com 2 e 4 workers o ganho continua perto do ideal, mas com o custo real do modelo o mestre vira gargalo muito antes. Além disso, 1000 fotos levariam cerca de 1 minuto num único notebook com a latência medida na 04, então o cluster só se justifica para um volume maior que o pico de um bairro, como a cidade inteira ou quadros de vídeo de inspeção. Para confirmar, basta repetir os dois cenários com 600 MFLOPS no lugar de 2000.
