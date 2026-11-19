# STT: resultados

## Comparação entre modelos

| Modelo | Áudios | WER global | WER médio por áudio | Latência média (s) |
|---|---|---|---|---|
| faster-whisper-base | 20 | 0.183 | 0.172 | 1.44 |
| faster-whisper-small | 20 | 0.175 | 0.190 | 5.09 |

WER global soma os erros de todas as palavras. Quanto menor, melhor.

## Viés: Falante

| Falante | WER faster-whisper-base | WER faster-whisper-small |
|---|---|---|
| A | 0.252 (n=10) | 0.307 (n=10) |
| B | 0.040 (n=5) | 0.000 (n=5) |
| C | 0.147 (n=5) | 0.147 (n=5) |

## Viés: Ruído de fundo

| Ruído de fundo | WER faster-whisper-base | WER faster-whisper-small |
|---|---|---|
| nao | 0.137 (n=15) | 0.191 (n=15) |
| sim | 0.280 (n=5) | 0.189 (n=5) |

## Cinco piores transcrições

| Modelo | Arquivo | WER | Referência | Transcrição |
|---|---|---|---|---|
| faster-whisper-small | stt_04.wav | 1.800 | Quem ganhou o jogo ontem? | O que é que é que é que é? |
| faster-whisper-base | stt_07.wav | 0.667 | Quais documentos eu levo ao CRAS? | Quais documentos eu levava para o Krais? |
| faster-whisper-small | stt_07.wav | 0.500 | Quais documentos eu levo ao CRAS? | Quais documentos eu levo para o CRICE? |
| faster-whisper-base | stt_04.wav | 0.400 | Quem ganhou o jogo ontem? | Quem ganhou o jogo de onde? |
| faster-whisper-base | stt_18.wav | 0.400 | O que são os PEVs? | E o que são os peves? |