# Avaliação de chunking e recuperação (BM25)

21 perguntas com evidência esperada (R01-R17, C01-C04) e 5 sem resposta (S01-S05).

## Acerto por configuração de chunking

| Config | Chunks | Doc@1 | Doc@3 | Doc@5 | Evid@1 | Evid@3 | Evid@5 | MRR |
|---|---|---|---|---|---|---|---|---|
| tam300_ov0 | 368 | 0.71 | 0.90 | 0.90 | 0.38 | 0.67 | 0.76 | 0.53 |
| tam800_ov120 | 154 | 0.81 | 0.90 | 0.90 | 0.71 | 0.81 | 0.81 | 0.75 |
| secao | 125 | 0.71 | 0.90 | 0.90 | 0.48 | 0.81 | 0.81 | 0.63 |

## Limiar de abstenção (score relativo do melhor trecho)

Falsa abstenção = pergunta respondível cujo melhor trecho fica abaixo do limiar. Falsa resposta = pergunta sem resposta cujo melhor trecho passa do limiar.

**tam300_ov0**

| Limiar | Falsa abstenção (R+C) | Falsa resposta (S) |
|---|---|---|
| 0.10 | 0.00 | 1.00 |
| 0.15 | 0.05 | 1.00 |
| 0.20 | 0.05 | 1.00 |
| 0.25 | 0.10 | 0.80 |
| 0.30 | 0.19 | 0.80 |
| 0.35 | 0.24 | 0.80 |
| 0.40 | 0.38 | 0.40 |
| 0.50 | 0.57 | 0.20 |

**tam800_ov120**

| Limiar | Falsa abstenção (R+C) | Falsa resposta (S) |
|---|---|---|
| 0.10 | 0.00 | 1.00 |
| 0.15 | 0.05 | 1.00 |
| 0.20 | 0.05 | 1.00 |
| 0.25 | 0.05 | 1.00 |
| 0.30 | 0.14 | 1.00 |
| 0.35 | 0.14 | 0.80 |
| 0.40 | 0.24 | 0.80 |
| 0.50 | 0.33 | 0.20 |

**secao**

| Limiar | Falsa abstenção (R+C) | Falsa resposta (S) |
|---|---|---|
| 0.10 | 0.00 | 1.00 |
| 0.15 | 0.05 | 1.00 |
| 0.20 | 0.05 | 1.00 |
| 0.25 | 0.05 | 1.00 |
| 0.30 | 0.14 | 1.00 |
| 0.35 | 0.19 | 1.00 |
| 0.40 | 0.19 | 0.80 |
| 0.50 | 0.29 | 0.40 |
