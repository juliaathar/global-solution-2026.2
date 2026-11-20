# Tarefas: RPA, Cluster e Visão Computacional

Legenda: [x] feito e verificado, [~] código escrito mas não executado, [ ] a fazer.

## RPA (`06-rpa`)

- [x] T1. Gerar dados sintéticos rotulados com casos problemáticos (`codigo/gerar_dados.py`)
- [x] T2. Ingestão do CSV com tratamento de arquivo ausente (`ingestao.py`)
- [x] T3. Validação de tamanho e campos (`validacao.py`)
- [x] T4. Deduplicação por similaridade de texto (`deduplicacao.py`)
- [x] T5. Classificação de categoria e urgência com confiança (`classificador.py`)
- [x] T6. Protocolo idempotente em SQLite (`armazenamento.py`)
- [x] T7. Notificação simulada com retry e espera exponencial (`notificador.py`)
- [x] T8. Fila de revisão humana para baixa confiança (`main.py`)
- [x] T9. Log e relatório de execução em JSON (`main.py`)
- [x] T10. Testes automatizados, 7 casos (`testes/test_rpa.py`)
- [x] T11. Medir acerto em amostra rotulada (`avaliar.py`)
- [x] T12. Definir os 3 temas da disciplina de RPA e preencher o quadro de temas no README
- [x] T13. Registrar um caso de falha demonstrado (print do log com retry) em `evidencias/` (9 cenários em `evidencias/falha_tratada.txt`)
- [~] T14. Ligar a saída do robô à API do app (`01-front-end/api`): a API tem `POST /protocolos` (contrato do robô) e `POST /protocolos/importar-rpa`, e o app usa a máscara, o classificador e o banco do robô; falta registrar uma execução do robô com `RPA_API_URL` apontando para a API real
- [x] T15. Escrever o parágrafo de proteção de dados, ética e ODS no README
- [x] T16. Melhorar o classificador (sinônimos como "sujeira" e "caçamba cheia" para lixo) ou trocar por modelo de ML da outra disciplina

Como executar, a partir de `06-rpa/codigo`:

```bash
python gerar_dados.py
python main.py
python avaliar.py
python -m unittest discover -s ../testes -v
```

Resultado medido na primeira execução (125 linhas: 120 relatos, 5 casos problemáticos):
95 protocolos, 17 duplicados, 3 inválidos, 10 enviados para revisão humana.
Acerto na amostra de 95 relatos rotulados: categoria 96,8% e urgência 90,5%.
Erros observados: palavras sem correspondência no dicionário (lixo classificado como urgência média) e conflito de palavra-chave (calçada contra lixo).
Limites: dados sintéticos gerados por modelos de frase, então o acerto real em relatos de cidadãos deve ser menor.
A deduplicação compara cada texto com todos os anteriores, o que fica lento em volumes grandes (12 s para 125 linhas) e pode marcar como duplicados textos parecidos de endereços diferentes.

## Visão Computacional (`04-visao-computacional`)

- [x] V1. Preparar dados com amostra e separação por blocos, sem vazamento (`codigo/preparar_dados.py`)
- [x] V2. Pré-processamento e aumento de dados (`dados.py`)
- [x] V3. Treinar MobileNetV2 com transferência de aprendizado (`treinar.py`)
- [x] V4. Avaliar com precisão, recall, F1 e matriz de confusão (`avaliar.py`)
- [x] V5. Função de inferência para a API, com limiar e aviso de triagem (`inferir.py`)
- [x] V6. Medir latência média e FPS em vídeo ou pasta de imagens (`benchmark_video.py`)
- [x] V7. Baixar o dataset Concrete Crack (Mendeley) e extrair em `imagens/Positive` e `imagens/Negative`
- [x] V8. Instalar dependências (`pip install -r codigo/requirements.txt`) e rodar V1 a V4
- [x] V9. Analisar erros do `erros_teste.csv` (sombra, textura, iluminação) e anotar no relatório (erros e acertos vistos em imagem, interferências simuladas em `montagem_interferencias.png`, sem fotos reais por decisão do grupo; anotado na seção 6 do relatório)
- [~] V10. Gravar ou escolher um vídeo curto e rodar V6, anotando equipamento e resolução (rodado com vídeo sintético em `evidencias/benchmark.txt`; repetir com vídeo real)
- [x] V11. Criar o endpoint de imagem na API e a tela no app
- [x] V12. Justificar arquitetura, pré-processamento e limiar de confiança no relatório (`04-visao-computacional/relatorio/relatorio_visao.md`; latência de vídeo real a preencher)
- [x] V13. Gravar o vídeo da funcionalidade integrada (https://www.youtube.com/watch?v=sOFx6vsD0AY)

Atenção: o dataset não informa a imagem original de cada recorte. A separação por blocos é uma aproximação e deve aparecer como limitação.
Executado em 2026-11-17 (CPU i5-6300U): teste com 600 imagens, acurácia 98,2%, F1 0,98 por classe, 11 erros. Limiar 0,45 escolhido na validação. Detalhes em `04-visao-computacional/README.md`.
Novos scripts: `escolher_limiar.py`, `analisar_erros.py`, `exemplos_acertos.py`, `teste_robustez.py`. Integração: `01-front-end/api/routers/visao.py` e `01-front-end/web/features/visao.py`.

## Cluster (`07-cluster`)

- [x] C1. Definir a carga, os parâmetros e os dois cenários (`cenarios_ispd/parametros.md`)
- [x] C2. Script para calcular redução percentual, razão T2/T4 e eficiência (`calcular_resultados.py`)
- [x] C3. Instalar o iSPD e confirmar as unidades de cada campo
- [x] C4. Montar e executar o cenário A (2 workers) e salvar o `.imsx`
- [x] C5. Montar e executar o cenário B (4 workers), mudando só a quantidade
- [x] C6. Capturar Total Simulated Time e a aba Resources dos dois cenários
- [x] C7. Rodar `calcular_resultados.py T2 T4` e montar a tabela com unidades
- [x] C8. Redigir o relatório de 2 a 4 páginas com análise de gargalos e limites

Os parâmetros são hipóteses declaradas. A comparação com o custo da MobileNetV2 (cerca de 600 MFLOPS) e com a latência medida em V6 (cerca de 60 ms por imagem) está em `07-cluster/cenarios_ispd/parametros.md`.
