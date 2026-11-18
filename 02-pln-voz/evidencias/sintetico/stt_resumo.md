# STT: resultados

## Comparação entre modelos

| Modelo | Áudios | WER global | WER médio por áudio | Latência média (s) |
|---|---|---|---|---|
| faster-whisper-base | 20 | 0.114 | 0.138 | 2.11 |
| faster-whisper-small | 20 | 0.066 | 0.067 | 6.86 |

WER global soma os erros de todas as palavras. Quanto menor, melhor.

## Viés: Falante

| Falante | WER faster-whisper-base | WER faster-whisper-small |
|---|---|---|
| Antonio | 0.141 (n=7) | 0.082 (n=7) |
| Francisca | 0.208 (n=7) | 0.098 (n=7) |
| Thalita | 0.052 (n=6) | 0.012 (n=6) |

## Viés: Ruído de fundo

| Ruído de fundo | WER faster-whisper-base | WER faster-whisper-small |
|---|---|---|
| nao | 0.138 (n=15) | 0.060 (n=15) |
| sim | 0.137 (n=5) | 0.087 (n=5) |

## Cinco piores transcrições

| Modelo | Arquivo | WER | Referência | Transcrição |
|---|---|---|---|---|
| faster-whisper-base | stt_01.wav | 0.600 | Que horas a UBS abre? | que horas ao B.S. abre. |
| faster-whisper-small | stt_11.wav | 0.333 | Tem um buraco na minha rua. Como eu aviso? | tem um buraco na minha rua, com o meu aviso. |
| faster-whisper-base | stt_13.wav | 0.286 | Como eu relato lixo acumulado na calçada? | Come o relato lixo acumulado na calçada. |
| faster-whisper-base | stt_14.wav | 0.250 | O relato gera um protocolo para eu acompanhar? | O relato já era um protocolo para eu acompanhar? |
| faster-whisper-base | stt_04.wav | 0.222 | Preciso do cartão do SUS para ir à UBS? | Preciso do cartão do SUS para ir ao BS? |