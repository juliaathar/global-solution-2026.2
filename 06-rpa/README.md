# 06 RPA e IA: robô do EloBairro

Robô que pega os relatos confirmados pelo cidadão (buraco, iluminação, lixo, calçada, alagamento, saúde), valida, remove duplicados, classifica categoria e urgência, gera um protocolo e notifica. O que o robô não resolve vai para revisão humana.

**Integrantes:**

| Nome completo | RM |
|---|---|
| Bruno Fernandes | 566325 |
| Edgar Lódula | 565260 |
| Júlia Aben-Athar | 566325 |

## Como executar
Requer Python 3.10+. Instale as dependências uma vez (`beautifulsoup4`, `lxml`, `requests`) e rode a partir de `06-rpa/codigo`:

```bash
pip install -r ../requirements.txt
python gerar_dados.py              # dados sintéticos rotulados (125 linhas)
python main.py                     # robô completo (ponto de entrada)
python avaliar.py                  # acerto na amostra sintética
python avaliar_independente.py     # acerto na amostra escrita à mão (desenvolvimento e teste)
python demonstrar_falha.py         # falhas tratadas, grava evidencias/falha_tratada.txt
python -m unittest discover -s ../testes -v
```

Pipeline: `relatos.csv → ingestão (+ crawler de notícias opcional) → validação → deduplicação → classificação → (saúde: coleta web de UBS; alagamento: aviso do Inmet) → protocolo (SQLite) → notificação com retry`, com `saida/revisao_humana.csv` e `saida/relatorio_execucao.json`.

## Configuração
Tudo por variáveis de ambiente, sem chaves no código. Não há chave de API: o robô usa regras e SQLite, sem LLM.

| Variável | Padrão | Função |
|---|---|---|
| `RPA_ENTRADA` | `dados_sinteticos/relatos.csv` | CSV de entrada |
| `RPA_CONFIANCA_MINIMA` | `0.5` | abaixo disso, vai para revisão humana |
| `RPA_SIMILARIDADE` | `0.85` | limiar de duplicado |
| `RPA_TENTATIVAS` / `RPA_ESPERA_BASE` | `3` / `0.2` | retry com espera exponencial |
| `RPA_API_URL` | vazio | endpoint do app (`01-front-end/api`) que recebe o protocolo por POST JSON; vazio = notificação simulada |
| `RPA_TIMEOUT` | `5` | timeout (s) das chamadas HTTP |
| `RPA_UBS_URL` | lista de UBS de São José dos Campos | página pública raspada |
| `RPA_OFFLINE` | vazio | `1` usa só o snapshot local da página (sem rede) |
| `RPA_ESPERA_REQ` | `1` | espera (s) após cada requisição ao site |
| `RPA_USAR_NOTICIAS` | vazio | `1` liga o crawler do Arquivo de Notícias como fonte extra de relatos públicos |
| `RPA_MAX_PAGINAS` | `3` | limite de páginas do crawler |
| `RPA_INMET_URL` / `RPA_INMET_AREA` | feed RSS do Inmet / `Vale do Paraíba Paulista` | feed e mesorregião dos avisos |

## Quadro de temas
Temas da disciplina (BeautifulSoup4, seletores CSS, XPath e webcrawler) mais IA com regras e resiliência.

| Tema | Onde entra no fluxo | O que resolve |
|---|---|---|
| Web scraping com BeautifulSoup4 e seletores CSS | `coleta_web.extrair_css` (UBS), `coleta_noticias.extrair_css` (cartões `div.noticia-02`), tabela do CDATA em `coleta_inmet` | Lê a lista pública de UBS e os cartões do arquivo de notícias; transforma a tabela HTML dos avisos do Inmet em campos |
| XPath com `lxml` | `coleta_web.extrair_xpath`, `coleta_noticias.extrair_xpath`, `coleta_inmet.extrair_avisos` (`//item` no XML do RSS) | Mesma extração por `starts-with()`, `contains()`, `following-sibling`; lê o XML do feed do Inmet. CSS e XPath devolvem o mesmo resultado nas duas páginas HTML (testado) |
| Webcrawler | `coleta_noticias.rastrear` | Percorre `?pag=1..N` do Arquivo de Notícias de SJC com limite de páginas, espera entre requisições, parada quando a página não traz notícia nova e mantém o já coletado se uma página falhar |
| IA / NLP com regras | `classificador.py` e `coleta_web.sugerir_ubs` | Classifica categoria, urgência e confiança; nos relatos de saúde sugere a UBS pelo nome ou endereço citado |
| Resiliência e orquestração | `main.py`, `notificador.py`, `armazenamento.py`, `coleta_web.baixar` | robots.txt, User-Agent, timeout, retry com espera, snapshot local se o site cair ou mudar, protocolo idempotente, log e relatório JSON |
| Humano no circuito | `saida/revisao_humana.csv` | Casos ambíguos vão para uma pessoa |

**Por que CSS e XPath na mesma página:** o HTML da prefeitura é uma sequência plana de `<p>` sem id nem classe por unidade. O CSS percorre os parágrafos e agrupa em ordem; o XPath localiza o título pelo texto e lê os irmãos seguintes. Os dois divergiram quando telefone e horário vieram no mesmo `<p>` (UBS Novo Horizonte); a leitura por rótulo (`_campos`) resolveu para ambos.

**Fontes públicas:** [feed Alert-AS do Inmet](https://apiprevmet3.inmet.gov.br/avisos/rss) (RSS, licença "public domain" declarada no feed), [Arquivo de Notícias da Prefeitura de SJC](https://servicos.sjc.sp.gov.br/arquivonoticias/arquivo_noticias.aspx) (o formulário de busca tem reCAPTCHA e não é usado) e a página pública [Unidades básicas de saúde, Prefeitura de São José dos Campos](https://www.sjc.sp.gov.br/servicos/saude/unidades-basicas-de-saude-ubs/unidades-basicas-de-saude/) (sem `robots.txt`, HTML estático). `dados_sinteticos/` guarda snapshots das três fontes (`ubs_sjc_snapshot.html`, `inmet_avisos_snapshot.xml`, `arquivo_noticias_pag1.html` e `pag2`), usados como caminho seguro e nos testes. O snapshot do Inmet tem avisos de 07 a 18/11/2026: depois dessa data nenhum aviso estará "vigente" e o robô vai tratar como sem alerta. O mapa das fontes testadas e descartadas está em `relatorio/mapa_fontes.md`.

**Execução com tudo ligado:** `RPA_USAR_NOTICIAS=1 python main.py`. Medido em 16/11/2026 com rede: 36 notícias em 3 páginas, 1 relevante (o arquivo é antigo e fala pouco de zeladoria); 86 avisos do Inmet, 3 vigentes para o Vale do Paraíba; 14 relatos de alagamento receberam o alerta. Os relatos de cidadãos continuam sintéticos.

## Evidências (`evidencias/`)
- `relatorio_execucao.json`: execução com 125 linhas (16/11/2026, com rede): 104 protocolos, 17 duplicados, 3 inválidos, 1 em revisão humana.
- `avaliacao_amostra_sintetica.txt`: 104/104 em categoria e urgência. **Resultado inflado**: os relatos e o dicionário foram escritos juntos, então 100% mostra que o fluxo funciona, não que o classificador generaliza.
- **Amostra independente** (`dados_sinteticos/amostra_independente.csv`): 60 relatos escritos à mão por nós, em linguagem de cidadão, fora do gerador, 30 de desenvolvimento e 30 de teste. Não são relatos reais de moradores.

| Grupo | Categoria | Urgência | Enviados à revisão humana |
|---|---|---|---|
| Antes de melhorar (60) | 46/60 = 76,7% | 40/60 = 66,7% | 24 |
| Desenvolvimento, depois (30) | 30/30 = 100% | 29/30 = 96,7% | 5 |
| **Teste, depois (30)** | **27/30 = 90,0%** | **26/30 = 86,7%** | 8 |

  `avaliacao_amostra_independente_antes.txt` e `avaliacao_amostra_independente.txt` guardam as listas de erros. **Método e ressalva:** o vocabulário novo (ex.: "esburacad", "luminaria", "boca de lobo", "medico") saiu só dos erros do grupo de desenvolvimento, e o grupo de teste não foi usado para escolher termos. Mesmo assim a lista de erros do teste foi impressa na primeira medição, então o resultado de 90% é otimista; só uma amostra nova, escrita por outra pessoa, mediria de verdade.
- **Análise dos erros.** Antes: 14 dos 14 erros de categoria eram relatos sem palavra conhecida, que caíam em "indefinido" e iam à revisão humana (caminho seguro), e os erros graves eram de urgência: alagamento saía "média". Depois da melhoria restam, no teste, 3 erros de categoria (todos "indefinido", ou seja, revisão humana: "valas", "alagado", "galeria de água") e 4 de urgência. Confusões entre categorias não apareceram. Limite principal: o classificador só reconhece palavras que já viu, e a urgência de buraco ("quebrou o eixo") escapa.
- Efeito nos dados sintéticos: os relatos em revisão humana caíram de 10 para 1 (a maioria era "esburacada", "escuridão" e perguntas de saúde com "médico" que o dicionário antigo não conhecia), e a busca passou a casar só no início de palavra, o que evita acerto no meio de outra palavra.
- `falha_tratada.txt`, 8 cenários: arquivo ausente, API do app fora do ar (3 tentativas com espera crescente, depois segue sem notificar), site de UBS fora do ar, `robots.txt` proibindo o acesso (portal de dados da Prefeitura de SP, `Disallow: /`), HTML que mudou, feed do Inmet fora do ar, feed com XML inválido e crawler que perde a página 2. O robô registra o erro e usa o snapshot ou mantém o já coletado.
- 30 testes automatizados: idempotência, retry, equivalência CSS × XPath, coleta de UBS, Inmet (região, vigência, XML inválido), crawler (limite, falha no meio), máscara de dados pessoais (inclusive que nada vaza para o banco, o relatório e a revisão humana), urgência do Inmet gravada no banco e piso de 90% de categoria na amostra independente.
- Reprodutibilidade: copiei `06-rpa` para uma pasta nova, criei um ambiente virtual, instalei `requirements.txt` e rodei os comandos acima. Tudo funcionou sem ajuda (16/11/2026).

**Limites:** o aviso do Inmet vale para a mesorregião, não para o bairro, e pode superestimar o risco local; as notícias do arquivo não são relatos de cidadãos (só títulos, de 2020 a 2024); a lista de UBS é de uma só cidade e os relatos sintéticos citam ruas inventadas, então a sugestão de UBS quase sempre cai em "consulte a lista"; a amostra independente foi escrita pelo próprio grupo; o classificador depende de palavras-chave e não entende contexto; a máscara de dados pessoais cobre CPF, e-mail, telefone, CEP e nome dito como "me chamo ...", mas não pega nome solto nem endereço completo. Trocar por um modelo treinado (disciplina de ML/NLP) é o próximo passo natural.

## Proteção de dados, ética e ODS
O protótipo usa apenas dados sintéticos. Um relato real pode trazer nome, telefone, e-mail ou CPF, então o robô mascara esses padrões (`privacidade.py`) logo depois da validação, antes de deduplicar, classificar, gravar ou registrar em log; só o texto mascarado circula, e o banco guarda apenas id, categoria, urgência e protocolo. Nenhum texto vai a API externa e não há LLM em nuvem; as fontes web são consultadas só para ler dados públicos. A máscara é por padrões e não pega todo dado pessoal, por isso em produção seria preciso revisão humana e um aviso ao cidadão. A classificação automática pode errar, então decisões de baixa confiança passam por pessoa e a urgência nunca é a única base para priorizar atendimento. Há risco de bairros que relatam menos ficarem invisíveis; os relatos devem ser monitorados por região. O aviso do Inmet vale para a região inteira e pode inflar a urgência local. Contribui para o ODS 11 (cidades e comunidades sustentáveis), ao agilizar a resposta a problemas urbanos, e para o ODS 16 (instituições eficazes e transparentes), pelo protocolo rastreável.
