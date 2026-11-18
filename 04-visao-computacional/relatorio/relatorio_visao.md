# Relatório: Visão Computacional para Manutenção Urbana

Projeto EloBairro, Global Solution 2026.2 (FIAP, CitizenTech). Disciplina de Visão Computacional.
Integrantes: Bruno Fernandes Nascimento (RM 552574), Edgar Lódula de Assis (RM 565260) e Júlia Aben-Athar (RM 566325).

> **Aviso de triagem.** O módulo sinaliza locais que merecem inspeção. A presença de fissura na imagem, isoladamente, **não define a gravidade do dano nem a segurança estrutural** da edificação. Esse aviso aparece na resposta da API (`aviso`) e fixo na tela do app.

## 1. Objetivo e escopo

Classificar fotos de superfícies de concreto em **com fissura** e **sem fissura**, devolvendo o rótulo e a confiança do modelo, para apoiar a triagem de inspeções pela prefeitura. O módulo está integrado ao app (endpoint de imagem, endpoint de vídeo e tela) e processa um vídeo curto para simular monitoramento urbano.

## 2. Dados e preparação

- **Base:** Concrete Crack Images for Classification (Mendeley, METU Campus). 40 mil imagens de 227×227 px, 20 mil por classe, recortadas de 458 fotos de alta resolução.
- **Amostra:** 2000 imagens por classe (4000 no total), para caber no prazo de quatro horas.
- **Pré-processamento:** redimensionamento para 224×224 e normalização com média e desvio do ImageNet, porque o modelo base foi pré-treinado nesses valores. No treino há aumento de dados: giros horizontal e vertical e variação de brilho e contraste (±30%), que imitam mudanças de enquadramento e de luz. Validação e teste só são redimensionados e normalizados.
- **Separação sem vazamento:** o dataset não informa de qual foto original veio cada recorte. Arquivos de numeração próxima tendem a vir da mesma foto, então a separação é feita por **blocos de 100 arquivos consecutivos**: o bloco inteiro vai para um único conjunto. O script checa que nenhum bloco aparece em dois conjuntos. Resultado: **2800 imagens de treino, 600 de validação e 600 de teste** (70/15/15). Isso é uma aproximação, não uma garantia (ver limitações).

## 3. Modelo

- **Arquitetura:** MobileNetV2 pré-treinada no ImageNet, com o extrator de características **congelado**; só a camada final (2 classes) é treinada.
- **Por que MobileNetV2:** é leve (cerca de 3,5 milhões de parâmetros e 0,3 bilhão de multiplicações-somas por imagem), roda em CPU e permite processar vídeo sem GPU. Para uma triagem em que a velocidade importa, o ganho de um modelo maior não compensaria a perda de FPS, e a base já é bem separável (ver seção 5).
- **Por que congelar o extrator:** com 2800 imagens de treino, treinar a rede inteira arriscaria sobreajuste e levaria mais tempo na CPU. A transferência de aprendizado usa o que o ImageNet já aprendeu (bordas, texturas).
- **Treino:** Adam, taxa 1e-3, lotes de 32, 5 épocas, semente 42, em CPU (cerca de 165 a 280 s por época). A melhor época pela acurácia de validação foi salva.

| Época | Perda de treino | Acurácia de validação |
|---|---|---|
| 1 | 0,331 | 0,973 |
| 2 | 0,134 | 0,975 |
| 3 | 0,097 | 0,985 |
| 4 | 0,083 | 0,982 |
| 5 | 0,073 | **0,987** |

## 4. Limiar de confiança

O app recomenda inspeção quando P(fissura) ≥ limiar. Como se trata de triagem, **deixar passar uma fissura custa mais do que inspecionar um local sem problema**. O critério, definido antes de olhar os números, foi: entre os limiares com **recall ≥ 0,99 na validação**, escolher o de maior precisão. O limiar foi escolhido **na validação**; o teste só foi usado depois, para medir.

| Limiar | Precisão (validação) | Recall (validação) | Falsos negativos | Falsos positivos |
|---|---|---|---|---|
| 0,30 | 0,961 | 0,997 | 1 | 12 |
| 0,40 | 0,977 | 0,997 | 1 | 7 |
| **0,45** | **0,984** | **0,993** | **2** | **5** |
| 0,50 | 0,990 | 0,983 | 5 | 3 |
| 0,70 | 0,997 | 0,957 | 13 | 1 |
| 0,90 | 1,000 | 0,917 | 25 | 0 |

Foi escolhido **0,45**. Limiares mais baixos aumentam os falsos alarmes sem ganho relevante de recall, e limiares altos deixam passar fissuras (43 falsos negativos em 600 com limiar 0,9, no teste). A tela permite ajustar o limiar.

## 5. Resultados no conjunto de teste (600 imagens)

Limiar 0,45. Todas as métricas abaixo foram medidas **no teste**, que não participou do treino nem da escolha do limiar.

| Classe | Precisão | Recall | F1 | Imagens |
|---|---|---|---|---|
| sem_fissura | 0,9898 | 0,9733 | 0,9815 | 300 |
| com_fissura | 0,9738 | 0,9900 | 0,9818 | 300 |

Acurácia de **98,17%** (589 acertos, 11 erros).

Matriz de confusão (`evidencias/matriz_confusao.png`):

| | Previsto sem fissura | Previsto com fissura |
|---|---|---|
| **Real sem fissura** | 292 | 8 (falsos positivos) |
| **Real com fissura** | 3 (falsos negativos) | 297 |

No limiar 0,5 o F1 é o mesmo (0,9818), com 4 falsos negativos e 7 falsos positivos. A diferença do 0,45 é metodológica: o limiar tem justificativa e trocou 1 falso negativo por 1 falso positivo.

**Atenção:** o teste vem da mesma distribuição do treino (fotos de prédios de um único campus), então 98% é um número **otimista** para fotos de cidadãos em outros lugares.

## 6. Análise de acertos e erros

As figuras estão em `evidencias/montagem_erros.png` e `evidencias/montagem_acertos.png`.

**Os 11 erros, vistos na imagem:**

| Tipo | Arquivos | O que se vê |
|---|---|---|
| Possível erro de rótulo | `13047`, `03043`, `00320` | Têm fissura ou trinca visível, mas estão em `Negative`. O modelo provavelmente acertou. |
| Falso positivo por textura | `13056`, `03097`, `00355`, `00375`, `00324` | Superfície sem fissura, com manchas claras, bolhas ou rugosidade riscada em diagonal. |
| Falso negativo por fissura fina ou de baixo contraste | `16429_1`, `09902`, `05342` | Fissura estreita, clara ou ocupando só um canto, com P(fissura) de 0,15 a 0,40. |

Mesmo entre os acertos há casos "apertados" (`montagem_acertos.png`): fissuras finas acertadas com P(fissura) próxima do limiar, e superfícies sem fissura com traços escuros que o modelo ainda classificou corretamente. Um deles (`00361`) também tem fissura visível rotulada como "sem fissura", outro indício de ruído nos rótulos.

**Interferências simuladas.** Não foram usadas fotos reais. Aplicamos sombra, pouca luz, superexposição, desfoque, baixa resolução, compressão JPEG e obstáculo às imagens do teste (`evidencias/robustez.csv`):

| Perturbação | Precisão | Recall | F1 |
|---|---|---|---|
| original | 0,977 | 0,987 | 0,982 |
| obstáculo central | 0,977 | 0,970 | 0,973 |
| sombra | 0,878 | 0,980 | 0,926 |
| JPEG de baixa qualidade | 0,965 | 0,923 | 0,944 |
| baixa resolução | 0,984 | 0,830 | 0,901 |
| superexposta | 1,000 | 0,727 | 0,842 |
| desfoque | 0,947 | 0,710 | 0,811 |
| pouca luz | 0,866 | 0,733 | 0,794 |

Essa tabela foi medida com o limiar 0,5, antes de adotarmos 0,45. O padrão é claro: **sombra gera falsos positivos** (a precisão cai para 0,878), e **pouca luz, excesso de luz e desfoque derrubam o recall**, ou seja, o modelo deixa de ver fissuras. O obstáculo central quase não atrapalha. Em `evidencias/montagem_interferencias.png`, 6 imagens sorteadas (fissuras largas e nítidas) resistiram à maioria das interferências, com 1 erro em 36 casos; a queda média da tabela vem das fissuras finas.

**Exemplos qualitativos com imagens da internet.** Para ver o app com fotos de fora do dataset, usamos 4 imagens do Wikimedia Commons com licença aberta (créditos em `evidencias/fotos_internet/CREDITOS.md`; prints em `evidencias/prints/07` a `10`). São **exemplos, não uma avaliação**: o rótulo "esperado" foi atribuído por inspeção visual da equipe, sem verificação de especialista, e 4 imagens não permitem calcular métrica. Limiar 0,45.

| Imagem | O que mostra | Resultado do app | Leitura |
|---|---|---|---|
| `01_fissura_muro_concreto` | Fissura vertical em muro de blocos de concreto | Alerta, P(fissura) 91,4% | Acerto |
| `02_pavimento_rachado` | Calçada de concreto com rachaduras largas | Alerta, P(fissura) 86,6% | Acerto |
| `03_calcada_quebrada_rua` | Calçada com várias fissuras finas | **Sem alerta**, P(fissura) 21,0% | **Falso negativo**: fissuras finas e foto de cena aberta |
| `04_concreto_polido_agregados` | Concreto polido com pedras (agregados) expostas, sem fissura | **Alerta**, P(fissura) 73,5% | **Falso positivo**: textura com agregados |

Os dois erros combinam com o que já aparece no teste: fissura fina escapa (falso negativo) e textura irregular vira falso alerta. Isso reforça que o resultado serve só para triagem e precisa de conferência humana.

## 7. Integração ao app

- **API (FastAPI):** `POST /visao/imagem` recebe JPG ou PNG (até 5 MB) e `POST /visao/video` recebe MP4, AVI, MOV ou MKV (até 50 MB), analisando 1 a cada N quadros. Ambos aceitam o parâmetro `limiar`.
- **Resposta (Pydantic):** rótulo, confiança, probabilidade de fissura, `inspecao_recomendada`, limiar, latência e o aviso de triagem. O vídeo devolve ainda quadros analisados, quadros com alerta, latência média, FPS e a série de probabilidades.
- **Validação e erros tratados:** formato não suportado (415), arquivo vazio ou corrompido (422), arquivo grande demais (413), limiar fora da faixa (422) e modelo ausente (503). Na tela, API fora do ar mostra uma mensagem clara, sem travar.
- **Tela (Streamlit):** abas Imagem e Vídeo, aviso de triagem fixo, alerta colorido com ícone, métricas de confiança e probabilidade, aviso de "confiança baixa" abaixo de 70%, slider de limiar e gráfico de probabilidade por quadro no vídeo. Prints em `evidencias/prints/`.

## 8. Desempenho

**Equipamento:** Intel Core i5-6300U (2 núcleos, 4 threads, 2,4 GHz), 15,7 GB de RAM, Windows 10, **sem GPU dedicada** (Intel HD 520). Inferência em CPU com PyTorch 2.15, uma imagem por vez. Todos os quadros são redimensionados para 224×224 antes do modelo.

> **Estas medições usam entradas sintéticas** (imagens do teste montadas em sequência e em um vídeo de 640×480), porque ainda não há um vídeo real gravado. **[A PREENCHER: repetir com o vídeo real, informando a resolução dele.]**

| Entrada | Quadros | Resolução | Latência média | Mediana | FPS fim a fim |
|---|---|---|---|---|---|
| Sequência de imagens (3 execuções) | 200 | 227×227 | 67 a 91 ms | 60 a 64 ms | 10,9 a 14,8 |
| Vídeo sintético (4 execuções) | 120 | 640×480 | 79 a 253 ms | 56 a 136 ms | 3,8 a 12,1 |

A variação entre execuções é grande: é um notebook com CPU de baixa potência, e a latência média sofre com picos ocasionais, enquanto a mediana é estável (cerca de 60 ms). A tendência é de **cerca de 60 ms por imagem e de 10 a 15 FPS** quando a máquina está estável; as execuções mais lentas do vídeo mostram o efeito de outras cargas no computador. O arquivo `evidencias/benchmark.txt` traz todas as execuções, e a medição final deve ser repetida com a máquina ociosa e na tomada.

**Qualidade contra velocidade.** 10 a 15 FPS são suficientes para monitoramento por amostragem de quadros, que é o que o app faz (1 a cada N quadros). Para 30 FPS em tempo real seria preciso pular quadros ou usar GPU. A escolha da MobileNetV2 com 224×224 mantém o custo baixo; entradas maiores ou modelos mais pesados aumentariam a latência sem ganho claro, dado o desempenho atual.

## 9. Limitações

- A separação por blocos é uma **aproximação**: pode haver recortes da mesma foto original em conjuntos diferentes.
- O teste vem da **mesma distribuição do treino**; o desempenho em fotos de cidadãos, em outros locais, deve ser menor. As 600 imagens de teste formam apenas **6 blocos de 100** (3 por classe) e imagens do mesmo bloco são parecidas, então o número efetivo de amostras independentes é bem menor que 600 e os 98% têm mais incerteza do que o tamanho do teste sugere.
- Há **rótulos duvidosos** no dataset (fissuras visíveis em `Negative`).
- **Não houve avaliação com fotos reais.** As interferências (sombra, pouca luz, desfoque, obstáculo) são **simuladas** sobre imagens do dataset. As 4 imagens da internet da seção 6 são só exemplos qualitativos, com rótulo atribuído visualmente.
- O modelo foi treinado com recortes quadrados de superfície vista **de perto**. Fotos de fachada inteira, de longe, e fotos retangulares redimensionadas à força para 224×224 podem degradar o resultado.
- **Classificação binária:** não localiza a fissura nem mede gravidade, abertura ou segurança estrutural.
- Latência e FPS foram medidos em um único equipamento e, por ora, com entradas sintéticas.

## 10. Reprodução e arquivos

Código em `codigo/`, notebook em `notebooks/vc_colab.ipynb`, evidências em `evidencias/`. Passo a passo e roteiro do vídeo de demonstração em `GUIA_FOTOS_E_VIDEO.md`. Comandos:

```bash
python preparar_dados.py
python treinar.py
python escolher_limiar.py
python avaliar.py
python analisar_erros.py
python exemplos_acertos.py
python teste_robustez.py
python exemplos_interferencias.py
python benchmark_video.py caminho/do/video.mp4
```

Referência do dataset: Özgenel, Ç. F.; Gönenç Sorguç, A. *Performance Comparison of Pretrained Convolutional Neural Networks on Crack Detection in Buildings*. ISARC 2018.
