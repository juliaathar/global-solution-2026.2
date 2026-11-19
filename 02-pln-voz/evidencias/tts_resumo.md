# TTS: nota geral dada por 6 avaliadores em 3 duplas

Cada dupla (um integrante do grupo e um familiar) deu uma nota geral a cada áudio, em escala de 1 a 10, convertida para 1 a 5 por `1 + (nota - 1) * 4 / 9`. **Naturalidade e clareza não foram avaliadas separadamente.** A avaliação foi cega (áudios embaralhados, com nomes neutros e mesmo formato).

| Motor | Áudios | Notas | Nota geral média (1-5) | Desvio padrão | Mínima | Máxima | Síntese média (s) |
|---|---|---|---|---|---|---|---|
| edge-tts | 10 | 30 | 4.30 | 0.52 | 3.67 | 5.00 | 2.31 |
| piper | 10 | 30 | 4.26 | 0.46 | 3.67 | 5.00 | 1.13 |

## Média por dupla

| Motor | Dupla 1 | Dupla 2 | Dupla 3 |
|---|---|---|---|
| edge-tts | 4.29 | 4.29 | 4.33 |
| piper | 4.42 | 4.02 | 4.33 |

## Comparação pareada (mesma frase nos dois motores)

Em 10 frases: `edge-tts` teve nota maior em 5, `piper` em 4 e houve empate em 1. Diferença média (edge-tts menos piper): +0.04 ponto na escala de 1 a 5.


## Limites

- Uma nota geral por áudio: não separa naturalidade de clareza, que o enunciado pede.
- A nota de cada dupla já é uma média arredondada para inteiro (1 a 10); isso soma até ±0,22 ponto na escala de 1 a 5.
- Os avaliadores são os integrantes do grupo e familiares, e não são independentes do trabalho.
- 10 áudios por motor: diferenças pequenas entre os motores não são conclusivas.