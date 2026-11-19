# TTS: inteligibilidade medida pelo Whisper

Cada áudio sintetizado foi transcrito pelo faster-whisper `small` e comparado ao texto falado. Mede se uma máquina reconhece a fala; **não** mede naturalidade nem substitui as notas de pessoas.

| Motor | Áudios | WER médio | WER máximo | Áudios sem nenhum erro |
|---|---|---|---|---|
| edge-tts | 10 | 0.055 | 0.125 | 3 |
| piper | 10 | 0.097 | 0.312 | 4 |

## Cinco maiores erros

| Motor | Id | WER | Texto falado | Transcrição |
|---|---|---|---|---|
| piper | r06 | 0.3125 | Você pode relatar um buraco na rua pelo EloBairro. Ele gera um protocolo para você acompan | Você pode relatar um poraco na rua pelo alo bairro e lhe gera um protocolo para você acomp |
| piper | r08 | 0.3077 | Fique tranquilo. Vou repetir devagar: primeiro, separe o R G. Depois, vá ao crás. | Fique tranquilo, vou repetir de VADAR primeiro, sepai o RG, depois vá ao CRAS. |
| piper | r03 | 0.1429 | O crás orienta sobre benefícios sociais e o Cadastro Único. Leve documento com foto. | O craz orienta sobre benefícios sociais e o cadastro único. Leve o documento com foto. |
| edge-tts | r06 | 0.125 | Você pode relatar um buraco na rua pelo EloBairro. Ele gera um protocolo para você acompan | Você pode relatar um buraco na rua pelo elo bairro, ele gera um protocolo para você acompa |
| edge-tts | r04 | 0.1111 | Em caso de emergência, ligue um nove dois para o samu ou um nove três para os Bombeiros. | Em caso de emergência, ligue o 9-2 para o SAMU ou o 9-3 para os bombeiros. |