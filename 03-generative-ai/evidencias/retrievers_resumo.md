# Comparação de retrievers

21 perguntas com evidência (R01-R17, C01-C04). Abstenção medida contra 9 perguntas sem evidência (A02, A03, D02, D03, S01, S02, S03, S04, S05).

AUC = chance de o sinal de uma pergunta respondível superar o de uma sem evidência (0,5 = acaso). Limiar, falsa abstenção (FA) e falsa resposta (FR) no ponto que maximiza 1 - FA - FR **neste mesmo conjunto** (otimista).

| Chunking | Retriever | Evid@1 | Evid@3 | Evid@5 | MRR | AUC abstenção | Limiar | FA | FR |
|---|---|---|---|---|---|---|---|---|---|
| tam300_ov0 | bm25 | 0.38 | 0.67 | 0.76 | 0.53 | 0.59 | 0.44 | 0.38 | 0.33 |
| tam300_ov0 | vet_minilm | 0.43 | 0.62 | 0.86 | 0.56 | 0.87 | 0.54 | 0.24 | 0.11 |
| tam300_ov0 | hib_minilm | 0.33 | 0.90 | 0.90 | 0.60 | 0.88 | 0.41 | 0.05 | 0.22 |
| tam300_ov0 | vet_e5large | 0.48 | 0.95 | 1.00 | 0.71 | 1.00 | 0.85 | 0.00 | 0.00 |
| tam300_ov0 | hib_e5large | 0.38 | 0.81 | 0.90 | 0.60 | 0.97 | 0.84 | 0.14 | 0.00 |
| tam800_ov120 | bm25 | 0.71 | 0.81 | 0.81 | 0.75 | 0.58 | 0.51 | 0.33 | 0.33 |
| tam800_ov120 | vet_minilm | 0.62 | 0.81 | 0.86 | 0.71 | 0.85 | 0.46 | 0.19 | 0.22 |
| tam800_ov120 | hib_minilm | 0.76 | 0.86 | 0.95 | 0.81 | 0.92 | 0.39 | 0.05 | 0.22 |
| tam800_ov120 | vet_e5large | 0.81 | 0.95 | 1.00 | 0.88 | 0.99 | 0.85 | 0.05 | 0.00 |
| tam800_ov120 | hib_e5large | 0.76 | 0.90 | 1.00 | 0.84 | 0.98 | 0.83 | 0.10 | 0.00 |
| secao | bm25 | 0.48 | 0.81 | 0.81 | 0.63 | 0.54 | 0.43 | 0.19 | 0.44 |
| secao | vet_minilm | 0.57 | 0.71 | 0.81 | 0.65 | 0.89 | 0.44 | 0.05 | 0.22 |
| secao | hib_minilm | 0.62 | 0.86 | 0.90 | 0.74 | 0.85 | 0.38 | 0.05 | 0.22 |
| secao | vet_e5large | 0.95 | 1.00 | 1.00 | 0.98 | 1.00 | 0.84 | 0.00 | 0.00 |
| secao | hib_e5large | 0.71 | 0.90 | 1.00 | 0.82 | 0.99 | 0.83 | 0.05 | 0.00 |