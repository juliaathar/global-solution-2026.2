# Resultados das simulações (iSPD)

Valores copiados da tela de resultados do iSPD. Parâmetros em `parametros.md`.

## Cenário A: 2 workers

| Métrica | Valor |
|---|---|
| Total Simulated Time | **1021,05 s** |
| Satisfaction | 100 % |
| Ociosidade dos recursos de processamento | 2,06 % |
| Ociosidade dos recursos de comunicação | 95,89 % |
| Eficiência (métrica do iSPD) | 0,25 % ("BAD") |
| Tempo médio de comunicação por tarefa | 0,0420 s |
| Tempo médio de fila de comunicação | 4,2e-05 s |
| Tempo médio de processamento por tarefa (relatório do iSPD) | 0,002 s (inconsistente com 2 s esperados; provável diferença de unidade no relatório, a investigar) |

### Aba Resources

| Recurso | Dono | Processamento realizado | Comunicação realizada |
|---|---|---|---|
| cluster0 node 1 | user1 | 1000,0 | 0,0 |
| cluster0 node 2 | user1 | 1000,0 | 0,0 |
| cluster0 (master/rede) | --- | 0,0 | 42,01 |

Leitura:
- Carga dividida igualmente entre os workers.
- Unidade do processamento não aparece no relatório. Inferência: GFLOPS (500 tarefas × 2000 MFLOPS = 1000 GFLOPS). Confirmar.
- Comunicação total de 42,01 s = 1000 × 0,042 s, cerca de 4 % do tempo total.
- Os 1021 s equivalem a 500 × 2 s de cálculo por worker mais cerca de 21 s de espera: com o Workqueue o master só envia a próxima tarefa depois de receber o retorno (500 × 0,042 s).

Evidências (em `../evidencias/`): `cenario_a_modelo.png`, `cenario_a_carga.png`, `cenario_a_resumo.png`, `cenario_a_task.png`, `cenario_a_resources.png`. Para o cenário B, os mesmos nomes com `cenario_b_`.
Arquivo do modelo: `cenario_a_2workers.imsx` (nesta pasta). O arquivo do cenário B (`cenario_b_4workers.imsx`) difere dele apenas em `nodes="4"`.

## Cenário B: 4 workers

Só o *Number of nodes* mudou (2 para 4). Carga e demais parâmetros iguais.

| Métrica | Valor |
|---|---|
| Total Simulated Time | **510,628 s** |
| Satisfaction | 100 % |
| Ociosidade dos recursos de processamento | 2,08 % |
| Ociosidade dos recursos de comunicação | 91,77 % |
| Eficiência (métrica do iSPD) | 0,25 % ("BAD") |
| Tempo médio de comunicação por tarefa | 0,0420 s |
| Tempo médio de fila de comunicação | 2,52e-04 s |
| Tempo médio de processamento por tarefa (relatório do iSPD) | 0,002 s (mesma inconsistência do cenário A) |

### Aba Resources

| Recurso | Dono | Processamento realizado | Comunicação realizada |
|---|---|---|---|
| cluster0 node 1 | user1 | 500,0 | 0,0 |
| cluster0 node 2 | user1 | 500,0 | 0,0 |
| cluster0 node 3 | user1 | 500,0 | 0,0 |
| cluster0 node 4 | user1 | 500,0 | 0,0 |
| cluster0 (master/rede) | --- | 0,0 | 42,01 |

Leitura:
- Carga dividida igualmente entre os 4 workers (500,0 cada, metade do valor por worker no cenário A).
- A comunicação total continua em 42,01 s, pois o número de tarefas e imagens é o mesmo. A rede ficou ocupada cerca de 8 % do tempo, contra 4 % no cenário A: ainda folgada, mas é o recurso que mais cresce em proporção ao aumentar workers.
- Fila de comunicação média subiu de 4,2e-05 s para 2,5e-04 s, sinal inicial de contenção no master, ainda desprezível.

## Comparação (calcular_resultados.py 1021.05 510.628)

| Métrica | Valor |
|---|---|
| T2 | 1021,05 s |
| T4 | 510,63 s |
| Redução percentual do tempo | 49,99 % |
| Razão T2/T4 | 2,000 (1,9996) |
| Speedup | 2,000 (ideal 2,0) |
| Eficiência | 100,0 % (99,98 %) |

Observação: o ganho é praticamente o ideal porque o cálculo domina (2 s por tarefa contra 0,042 s de comunicação). O pequeno desvio de 0,02 % vem da espera do Workqueue e da rede. Esse resultado é consequência dos parâmetros hipotéticos; se a comunicação fosse bem maior em relação ao cálculo, o master viraria gargalo.
