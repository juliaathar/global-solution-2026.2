# Parâmetros dos cenários iSPD (valores estimados e declarados)

A simulação é uma hipótese de carga do AcolheBairro, não uma medição do protótipo.
Confirme as unidades na interface do iSPD ao cadastrar cada campo.

## Carga de trabalho

Tarefa repetida: classificar fotos de fissuras e danos enviadas pelos cidadãos (módulo de Visão Computacional).
Cenário de pico: campanha de relatos após uma chuva forte.

| Parâmetro | Valor | Justificativa |
|---|---|---|
| Número de tarefas | 1000 imagens | pico de relatos em um dia |
| Tamanho computacional por tarefa | ~600 MFLOPS (estimado) | MobileNetV2 a 224x224 faz cerca de 300 milhões de multiplicações-somas por imagem |
| Comunicação por tarefa (envio) | ~0,4 Mbit (≈ 50 KB) | foto JPEG redimensionada |
| Comunicação por tarefa (retorno) | ~0,01 Mbit | rótulo e confiança |

Substitua pelo valor medido de `benchmark_video.py` se quiser aproximar do real, mas declare a origem.

## Infraestrutura (idêntica nos dois cenários)

| Parâmetro | Valor |
|---|---|
| Capacidade de cada worker | 2000 MFLOPS (estimado) |
| Escalonador | Round Robin (o mesmo nos dois) |
| Banda do enlace | 100 Mbit/s |
| Latência do enlace | 0,001 s |
| Mestre | 1, sem processamento de tarefas |

## Cenários

| Cenário | Workers | O que muda |
|---|---|---|
| A | 2 | somente a quantidade de workers |
| B | 4 | somente a quantidade de workers |

## Passo a passo no iSPD
1. Criar o modelo: 1 mestre, N workers e 1 rede, com os valores acima.
2. Configurar a carga: 1000 tarefas com o tamanho e a comunicação acima.
3. Escolher o escalonador (Round Robin) e executar.
4. Anotar o **Total Simulated Time (s)** e capturar a aba **Resources** (uso de cada worker).
5. Salvar o arquivo `.imsx` do modelo e as capturas nesta pasta, com nomes `cenario_a_2workers.*` e `cenario_b_4workers.*`.
6. Repetir com 4 workers sem alterar mais nada.
7. Calcular: `python calcular_resultados.py T2 T4`.

## Pontos para discutir no relatório
- Se T2/T4 ficar abaixo de 2, qual foi o gargalo (rede, mestre ou distribuição desigual).
- Se a banda ou o mestre limitar, o ganho de workers extras será pequeno. Isso também vale nota.
- Limites: capacidade e tamanho das tarefas são hipóteses, e o iSPD não modela memória nem I/O de disco.
