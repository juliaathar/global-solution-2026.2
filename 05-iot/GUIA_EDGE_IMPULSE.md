# Guia passo a passo: OuviAí no Edge Impulse

Tempo estimado: 1h30 a 2h. Tudo o que é parâmetro já está decidido aqui; os números que aparecerem na tela
vão para o relatório nos campos marcados com ⟨preencher⟩. Tire cada print assim que a tela aparecer e salve
em `evidencias/` com o nome indicado.

## 0. Antes de começar

- Conta gratuita em https://studio.edgeimpulse.com. Crie o projeto **OuviAi** (tipo: Audio).
- Combine com quem mora com você: vão ser gravados só a campainha, batidas na porta e sons da casa.
  **Não grave conversas** (veja "Privacidade" no relatório). Se alguém falar perto do celular, apague e grave de novo.
- Tenha à mão: a campainha (ou um vídeo/áudio de campainha tocando em outro aparelho), uma porta, e o celular.

## 1. Gravar os dados (Data acquisition)

Opção A, recomendada: direto do celular.

1. **Data acquisition > Connect a device > Use your mobile phone**. Leia o QR code com o celular.
2. No celular: sensor **Microphone**, **Sample length 5000 ms**, frequência **16000 Hz**.
3. Em **Label** escreva exatamente `campainha`, grave **20** vezes. Depois `batida_porta` (20) e `ambiente` (20).
4. Variação ajuda o modelo: mude a distância (1 m e 3 m), o cômodo e o volume. Para `batida_porta`, varie força
   e número de batidas. Para `ambiente`: TV baixa, cozinha, ventilador, passos, porta de armário, silêncio.
   Os sons de "ambiente" parecidos com batida (armário, panela) são os que mais ensinam o modelo a não errar.
5. Separe Training e Test: **Dashboard > Perform train / test split** (80/20 dá 16/4; o enunciado pede 15/5).
   Para ficar exato, em **Data acquisition > Test**, mova 5 amostras de cada classe com o menu ⋮ > *Move to test set*,
   até ficar 15 em Training e 5 em Test por classe.
6. Confira o rótulo de todas: clique em algumas e ouça.
7. 📸 `ei_01_data_acquisition.png`: a lista com as 3 classes e a contagem por classe (aba Training e aba Test).

Opção B: gravar no computador ou no gravador do celular e enviar por script.

```bash
cd 05-iot/codigo
pip install -r requirements.txt
# coloque as gravações em dados_audio/brutos/campainha, .../batida_porta, .../ambiente (20 em cada)
python preparar_audios.py        # 16 kHz, mono, PCM16, 5 s; sorteia 15 Training e 5 Test sem reuso
python verificar_dataset.py      # gera evidencias/verificacao_dataset.md
set EI_API_KEY=ei_...            # Dashboard > Keys
python enviar_edge_impulse.py --enviar
```

## 2. Impulse design

**Impulse design > Create impulse**:

| Bloco | Parâmetro | Valor |
|---|---|---|
| Time series data | Window size | 1000 ms |
| | Window increase (stride) | 500 ms |
| | Frequency | 16000 Hz |
| | Zero-pad data | ligado |
| Processing block | **Audio (MFE)** | |
| Learning block | **Classification** | saídas: ambiente, batida_porta, campainha |

📸 `ei_02_impulse_design.png`

**MFE** (deixe o padrão e confira):

| Parâmetro | Valor |
|---|---|
| Frame length | 0.02 s |
| Frame stride | 0.01 s |
| Filter number | 40 |
| FFT length | 256 |
| Low frequency | 0 |
| High frequency | 0 (= metade da taxa, 8 kHz) |
| Noise floor | -52 dB |

Clique **Save parameters > Generate features**. 📸 `ei_03_generate_features.png` com o *Feature explorer*
(os pontos de campainha devem formar um grupo separado; anote se batida e ambiente se misturam).

## 3. Classifier (CNN)

| Parâmetro | Valor |
|---|---|
| Number of training cycles | 100 |
| Learning rate | 0.005 |
| Validation set size | 20% |
| Data augmentation | ligado: *Add noise* = Low, *Mask time bands* = Low |
| Arquitetura | a padrão sugerida para áudio (confira na tela): Reshape (40 colunas) > 1D Conv 8 filtros + MaxPool > Dropout 0,25 > 1D Conv 16 filtros + MaxPool > Dropout 0,25 > Flatten > Dense (3 saídas) |

**Save & train**. Anote acurácia e loss de validação e a matriz de confusão.
📸 `ei_04_classifier.png` (inclua o bloco *Model: Last training performance* com a matriz e o *On-device performance*).

Se a acurácia de validação ficar abaixo de 85%: grave mais variação de `ambiente` parecida com batida, ou
aumente os ciclos para 200. Registre no relatório o que mudou.

## 4. Model testing

**Model testing > Classify all**. 📸 `ei_05_model_testing.png`.
Preencha `evidencias/model_testing.csv` (crie com `python avaliar.py modelos`) com o resultado de cada um dos
15 arquivos de Test e rode `python avaliar.py modelo`. Isso gera a matriz em `evidencias/resultado_model_testing.md`.

Os arquivos de Test **não podem** ter sido usados no treino: o Edge Impulse garante isso quando estão na aba Test.

## 5. Teste ao vivo no celular

1. **Deployment** (ou **Dashboard**) > **Run this model** > leia o **QR code** com o celular. Permita o microfone.
2. Faça as 15 tentativas de `evidencias/tentativas_ao_vivo.csv` (5 por classe; os sons sugeridos já estão lá).
   Para cada uma, anote a classe que apareceu e a confiança.
3. Rode `python avaliar.py ao-vivo`: gera a % de acertos, a matriz e a lista de falsos positivos.
4. 📸 `ei_06_celular_campainha.png` e `ei_07_celular_ambiente.png` (print da tela do celular).

## 6. Ligar ao EloBairro (opcional, para o vídeo)

- Sem celular: na interface, **Avisos da casa > Testar sem o celular**, ou `python ponte_alertas.py --simular`.
- Com o modelo de verdade, em Linux, macOS, Raspberry Pi ou WSL2: **Deployment > Linux (x86)** baixa o `.eim`;
  depois `pip install edge_impulse_linux pyaudio` e `python ponte_alertas.py --modelo ouviai.eim`.
  Toque a campainha: o alerta aparece em **Avisos da casa**.
