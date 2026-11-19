# 04 Visão Computacional para Manutenção Urbana

Legenda: [x] feito e verificado, [~] feito em parte, [ ] a fazer.

## Checklist
- [x] Base escolhida (Concrete Crack, SDNET2018 ou RDD2022) e amostra usada: Concrete Crack (Mendeley), 2000 imagens por classe
- [x] Pré-processamento (redimensionar, normalizar): 224x224, normalização ImageNet, aumento de dados só no treino
- [~] Treino/validação/teste sem vazamento entre recortes da mesma imagem: separação por blocos de 100 arquivos consecutivos, com checagem. É uma aproximação, pois o dataset não informa a imagem original
- [x] CNN, transferência de aprendizado ou detector de objetos: MobileNetV2 pré-treinada, extrator congelado
- [x] Métricas: precisão, recall, F1 e matriz de confusão (ou mAP, se detecção)
- [~] Análise de acertos e erros (sombra, textura, iluminação, obstáculos): erros e acertos do teste analisados em imagem; sombra, luz, desfoque e obstáculo analisados com interferências simuladas sobre imagens do teste (`montagem_interferencias.png`). Sem fotos reais: declarar como limitação
- [x] Funcionalidade no app: imagem com resultado e confiança
- [~] Processamento de vídeo curto ou sequência de imagens: funciona na API e na tela, testado só com vídeo sintético
- [~] Latência média por imagem e FPS, com equipamento e resolução: medido (CPU i5-6300U), mas com vídeo sintético. Repetir com vídeo real
- [x] Justificativa de arquitetura, pré-processamento e limiar de confiança (`relatorio/relatorio_visao.md`)
- [x] Aviso: fissura na imagem não define gravidade nem segurança estrutural: na API (`aviso`) e fixo na tela
- [x] Vídeo de demonstração e relatório breve: relatório em `relatorio/relatorio_visao.md` (a latência com vídeo real continua a preencher) e vídeo publicado como não listado no YouTube: https://www.youtube.com/watch?v=sOFx6vsD0AY

## Resultados medidos (conjunto de teste, 600 imagens)

Limiar 0,45, escolhido na **validação** (critério: recall >= 0,99 com maior precisão), depois medido no teste.

| Classe | Precisão | Recall | F1 |
|---|---|---|---|
| sem_fissura | 0,9898 | 0,9733 | 0,9815 |
| com_fissura | 0,9738 | 0,9900 | 0,9818 |

Acurácia 98,17%, com 11 erros (8 falsos positivos e 3 falsos negativos). No limiar 0,5 o resultado é parecido (F1 0,9818, 4 falsos negativos e 7 falsos positivos).

Desempenho em CPU (Intel Core i5-6300U, 2 núcleos, 15,7 GB, sem GPU): mediana de cerca de 60 ms por imagem e 10 a 15 FPS em sequência de 227x227; no vídeo sintético 640x480 a variação entre execuções é grande (3,8 a 12,1 FPS). Todas as execuções estão em `evidencias/benchmark.txt`. Entradas sintéticas montadas de imagens do teste: repetir com vídeo real.

Robustez com perturbações sintéticas (F1 no teste): original 0,982, obstáculo 0,973, sombra 0,926, JPEG ruim 0,944, baixa resolução 0,901, superexposta 0,842, desfoque 0,811, pouca luz 0,794.

## Limitações a declarar no relatório
- Separação por blocos é aproximação: pode haver recortes da mesma foto original em conjuntos diferentes.
- O teste vem da mesma distribuição do treino (fotos de prédios de um único campus), então 98% é otimista para fotos de cidadãos. Além disso, as 600 imagens de teste formam só 6 blocos de 100 (3 por classe), parecidas entre si dentro do bloco: o número efetivo de amostras independentes é bem menor que 600.
- Há rótulos duvidosos: imagens com fissura visível em `Negative` (por exemplo `13047`, `03043`, `00320`, `00361`).
- Pouca luz, excesso de luz e desfoque derrubam o recall; sombra e texturas manchadas geram falsos positivos.
- Nenhuma foto de cidadão foi avaliada: as interferências (sombra, pouca luz, desfoque, obstáculo) são simuladas sobre imagens do dataset. Há só 4 imagens da internet (Wikimedia Commons) como exemplo qualitativo, com rótulo atribuído visualmente: 2 acertos, 1 falso negativo (fissuras finas) e 1 falso positivo (agregados expostos). Créditos em `evidencias/fotos_internet/CREDITOS.md`.
- Classificação binária: não localiza a fissura e não mede gravidade.

## Como rodar (a partir de `codigo/`)

Antes, baixe o dataset (241 MB) em [Mendeley Data](https://data.mendeley.com/datasets/5y9wdsg2zt/1) e extraia em `04-visao-computacional/imagens/` com as pastas `Positive/` e `Negative/` (ou aponte `VC_IMAGENS`). O notebook `notebooks/vc_colab.ipynb` faz o download e confere o hash sozinho. Os dados não ficam no git, mas o **modelo treinado** (`codigo/modelo_fissuras.pt`) sim: é o mesmo que gerou as métricas deste README e do relatório, então a API e o app funcionam sem treinar. `treinar.py` só é preciso para retreinar. Em 18/11/2026 o treino foi refeito do zero em outra máquina (Linux, CPU, PyTorch 2.15, mesma semente e mesmo manifesto) e reproduziu as métricas deste README: acurácia de validação por época, 98,17% no teste e os mesmos 11 erros.

```bash
pip install -r requirements.txt
python preparar_dados.py        # amostra e separação
python treinar.py               # transferência de aprendizado
python escolher_limiar.py       # limiar escolhido na validação
python avaliar.py               # métricas no teste
python analisar_erros.py        # varredura de limiar no teste e montagem dos erros
python exemplos_acertos.py      # montagem dos acertos
python teste_robustez.py        # perturbações sintéticas
python exemplos_interferencias.py   # mesmas imagens com sombra, pouca luz, desfoque, obstáculo
python benchmark_video.py caminho/do/video.mp4
```

Integração, a partir de `01-front-end/`: `uvicorn api.main:app --port 8000` e `streamlit run web/app.py`.

## Evidências (`evidencias/`)
`relatorio_classificacao.txt`, `matriz_confusao.png`, `erros_teste.csv`, `montagem_erros.png`, `montagem_acertos.png`, `limiar_validacao.csv`, `limiar_escolhido.json`, `varredura_limiar.csv`, `robustez.csv`, `montagem_interferencias.png`, `interferencias_exemplos.csv`, `prints/` (telas do app, inclusive 07 a 10 com imagens da internet), `fotos_internet/` (imagens e créditos), `benchmark.txt`, `historico_treino.json`, `manifesto_split.csv`.
