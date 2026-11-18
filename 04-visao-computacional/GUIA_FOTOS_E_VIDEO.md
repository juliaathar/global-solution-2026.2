# Guia: fotos reais, vídeo real e roteiro do vídeo de demonstração

Os prints desta pasta (`evidencias/prints/`) mostram a tela do app funcionando. Eles usam **imagens do dataset**, não fotos reais, e servem só como referência do que aparece na tela.

## Parte A. O que você precisa fazer

### Item 3: fotos reais (OPCIONAL, decidido não fazer por enquanto)

**Decisão:** em vez de fotos reais, a análise de sombra, textura, luz e obstáculos usa imagens do conjunto de teste com interferências **simuladas** (`evidencias/montagem_interferencias.png`, `robustez.csv`). No relatório e no vídeo isso deve aparecer como **simulado, não foto real**, e a falta de fotos reais entra nas limitações. Os prints do app **não** devem ser apresentados como fotos reais: são capturas de tela com imagens do dataset.

Se mudar de ideia e quiser fotos reais, siga os passos abaixo.

1. **Tire 20 a 30 fotos** com o celular, de **perto** (30 a 60 cm), com a parede, muro ou calçada ocupando o quadro todo.
   - O modelo foi treinado com recortes de 227×227 px de superfícies vistas de perto. Foto de fachada inteira, de longe, faz a fissura virar um traço minúsculo, e o erro seria de escala, não do modelo.
2. **Distribuição sugerida** (ajuste ao que achar na rua):

   | Quantidade | Conteúdo | Sufixo no nome |
   |---|---|---|
   | 8 | Com fissura, boa luz, sem interferência | (nenhum) |
   | 4 | Sem fissura, boa luz, superfície lisa | (nenhum) |
   | 4 | Com ou sem fissura, com **sombra** na superfície | `__sombra` |
   | 3 | Pouca luz (fim de tarde, área coberta) | `__poucaluz` |
   | 3 | Galho, objeto ou cabo na frente | `__obstaculo` |
   | 4 | **Sem fissura**, mas com reboco, pintura descascada, manchas ou rejunte | `__textura` |
   | 2 | Contraluz | `__contraluz` |
   | 2 | Fachada inteira de longe (limite de escala) | `__longe` |

3. **Nome do arquivo**: comece com `com_` (tem fissura) ou `sem_` (não tem). Exemplos: `com_parede01.jpg`, `com_calcada02__sombra.jpg`, `sem_muro03__textura.jpg`. Você é quem decide o rótulo, olhando a foto.
4. **Evite** rostos, placas de carro, números de casas e pessoas (LGPD). Fotografe só superfícies.
5. Se possível, mantenha as fotos em JPG ou PNG, com no máximo 5 MB (limite do app).

**No Colab** (arquivo `notebooks/vc_colab.ipynb`):
1. Abra em colab.research.google.com (*Arquivo → Fazer upload de notebook*).
2. *Ambiente de execução → Alterar tipo → GPU T4* (opcional).
3. Na célula do modelo, escolha: treinar no Colab (padrão) ou enviar o seu `modelo_fissuras.pt` (`USAR_MODELO_LOCAL = True`). **Prefira enviar o seu**, para os números do relatório serem os mesmos que já medimos.
4. *Executar tudo*. Na célula 📷, selecione todas as fotos de uma vez.
5. Na última célula, baixe `evidencias_colab.zip` e coloque o conteúdo em `04-visao-computacional/evidencias/`.

O que o notebook gera para o relatório: `fotos_reais_resultados.csv`, `fotos_reais_matriz.png`, `fotos_reais_por_condicao.csv` (taxa de acerto por sombra, textura etc.) e `fotos_reais_grade.png` (cada foto com ACERTO ou ERRO).

Não testei as partes específicas do Colab (instalar pacote, baixar o dataset, `files.upload`). A lógica de análise das fotos foi testada localmente com imagens simuladas.

### Item 4: vídeo real para latência e FPS

1. **Grave 10 a 20 s** andando devagar (cerca de 20 cm/s) ao longo de uma parede, muro ou calçada, com a câmera a 30 a 60 cm. Inclua um trecho com fissura e um sem.
2. **Tamanho**: o app aceita até 50 MB. Vídeo de celular em 1080p pode passar disso. Grave em 720p ou comprima. **Anote a resolução** (ex.: 1280×720).
3. **Sem pessoas** no quadro.
4. **Meça no computador onde o app roda.** Esse é o equipamento que vale para o relatório (Intel Core i5-6300U, 15,7 GB, sem GPU):

   ```bash
   cd "<caminho-do-repositorio>\04-visao-computacional\codigo"
   C:\vcenv\Scripts\python.exe benchmark_video.py "C:\caminho\real\do\seu_video.mp4"
   ```

   Troque `C:\caminho\real\do\seu_video.mp4` pelo caminho verdadeiro do seu arquivo. Copie a saída (equipamento, resolução, latência média, FPS).
5. **Opcional:** repetir no Colab (célula 🎥) para ter uma segunda referência.
6. **Alternativa permitida pelo enunciado:** uma pasta de imagens em sequência no lugar do vídeo.
7. Me passe o caminho do vídeo e eu rodo o benchmark, gero o gráfico e atualizo o README e o documento de tarefas.

## Parte B. O que o vídeo de demonstração precisa ter

O enunciado pede: **demonstração da funcionalidade integrada, com exemplos de imagens e processamento de vídeo ou sequência de imagens**. O vídeo do front-end tem no máximo 5 min e deve mostrar problema, fluxo, código, erro tratado e evidências. O roteiro abaixo cobre os dois.

### Preparação (antes de gravar)
Em **dois terminais**, cada um começando com `cd` para a pasta `01-front-end` (rodar de outra pasta dá `No module named 'api'`).

Terminal 1 (API):

```bash
cd "<caminho-do-repositorio>\01-front-end"
C:\vcenv\Scripts\python.exe -m uvicorn api.main:app --port 8000
```

Terminal 2 (tela):

```bash
cd "<caminho-do-repositorio>\01-front-end"
C:\vcenv\Scripts\python.exe -m streamlit run web/app.py
```

Abra http://localhost:8501. Deixe à mão: 3 fotos (uma com fissura, uma sem, uma difícil), o vídeo real, e as imagens `matriz_confusao.png`, `montagem_erros.png`, `montagem_acertos.png`.

### Roteiro (cerca de 5 min)

| Tempo | O que mostrar | O que dizer |
|---|---|---|
| 0:00 a 0:30 | Tela do app, aviso amarelo no topo | O problema (fissuras e danos em prédios e vias públicas) e que o módulo faz **triagem de inspeção**, não diagnóstico. ODS 10 e 16. |
| 0:30 a 1:00 | Diagrama simples: foto → API `/visao/imagem` → MobileNetV2 → resposta → tela. Abrir `routers/visao.py` rapidamente. | Fluxo front/back separado, validação de entrada, resposta estruturada (Pydantic). |
| 1:00 a 2:15 | Aba Imagem: foto **com fissura** (alerta vermelho), foto **sem fissura** (verde), foto **difícil** (aviso de confiança baixa). Mexer no slider de limiar. | Mostrar confiança e probabilidade. Explicar o limiar 0,45: escolhido na validação, recall ≥ 0,99, porque perder fissura custa mais que uma inspeção a mais. |
| 2:15 a 3:15 | Aba Vídeo: enviar o **vídeo real**, analisar, mostrar gráfico, quadros com alerta e as métricas. | Equipamento, resolução, **latência média e FPS**. Por que MobileNetV2 (leve, roda em CPU) e por que amostrar 1 a cada N quadros. |
| 3:15 a 3:45 | **Erro tratado:** derrubar a API e enviar uma imagem (mensagem "Não foi possível conectar"), ou enviar um `.txt` (formato não suportado). | Mostrar que o app não quebra e avisa o usuário. |
| 3:45 a 4:30 | Evidências: matriz de confusão, métricas do teste, montagem de erros e de acertos, tabela de robustez, resultado das fotos reais. | Precisão, recall e F1 no **teste**. Falsos positivos com textura manchada, falsos negativos com fissura fina. Interferência de sombra e pouca luz. |
| 4:30 a 5:00 | Slide ou tela com as limitações | Divisão por blocos é aproximação, rótulos duvidosos no dataset, escala (foto de longe), classificação binária. **Fissura na imagem não define gravidade nem segurança estrutural.** |

### Checklist do que não pode faltar
- [ ] Aviso de triagem visível (a tela já tem um fixo).
- [ ] Resultado com **rótulo e confiança** em pelo menos 3 imagens (com fissura, sem fissura, difícil).
- [ ] Vídeo real processado, com **latência, FPS, equipamento e resolução** ditos ou na tela.
- [ ] Um **erro tratado**.
- [ ] **Matriz de confusão e métricas** do conjunto de teste.
- [ ] Pelo menos **um acerto e um erro** analisados, com a causa (sombra, textura, luz, obstáculo).
- [ ] **Justificativa** da arquitetura, do pré-processamento (224×224, normalização) e do limiar.
- [ ] **Limitações** ditas em voz alta.
- [ ] Cada integrante aparece ou fala (se a disciplina exigir).

## Prints de referência

| Arquivo | O que mostra |
|---|---|
| `evidencias/prints/01_tela_inicial.jpg` | Tela inicial com o aviso de triagem e o slider de limiar |
| `evidencias/prints/02_imagem_com_fissura.jpg` | Alerta de inspeção, confiança e probabilidade |
| `evidencias/prints/03_imagem_sem_fissura.jpg` | Resultado verde |
| `evidencias/prints/04_confianca_baixa.jpg` | Aviso de resultado incerto |
| `evidencias/prints/05_video_resultado.jpg` | Métricas, gráfico por quadro e lista de quadros com alerta (vídeo sintético) |
| `evidencias/prints/06_erro_api_fora_do_ar.jpg` | Erro tratado quando a API não responde |
| `evidencias/prints/07_internet_fissura_muro_alerta.png` | Imagem da internet: fissura em muro, alerta (91,4%) |
| `evidencias/prints/08_internet_pavimento_rachado_alerta.png` | Imagem da internet: calçada rachada, alerta (86,6%) |
| `evidencias/prints/09_internet_calcada_fissuras_finas_nao_detectou.png` | Imagem da internet: fissuras finas **não detectadas** (falso negativo, 21,0%) |
| `evidencias/prints/10_internet_concreto_com_agregados_falso_alerta.png` | Imagem da internet: concreto com agregados, **falso alerta** (73,5%) |

Os prints 07 a 10 usam imagens do Wikimedia Commons (créditos em `evidencias/fotos_internet/CREDITOS.md`). Servem para mostrar acertos e erros no vídeo, mas não são avaliação: 4 imagens, com rótulo atribuído visualmente.
