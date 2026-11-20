# EloBairro

Assistente de serviços públicos do bairro, feito para quem tem dificuldade com interfaces de texto: pessoas idosas, com baixa alfabetização, com deficiência visual, auditiva ou motora.

Projeto da Global Solution 2026.2 (FIAP, CitizenTech). Uma única solução atende nove disciplinas. Cada disciplina tem sua própria pasta, numerada de 01 a 09, com código, dados, notebooks, evidências e relatório daquela matéria.

## Integrantes

| Nome completo | RM |
|---|---|
| Bruno Fernandes Nascimento | 552574 |
| Edgar Lódula de Assis | 565260 |
| Júlia Aben-Athar | 566325 |

## Problema e público

Muitas pessoas não sabem onde conseguir um serviço público (UBS, CRAS, segunda via de documento, benefício), quais documentos levar, ou como reclamar de um problema no bairro, como um buraco ou uma calçada quebrada. Os canais existentes dependem de texto, de cadastro e de linguagem burocrática.

Público atendido: idosos, pessoas de baixa renda e pessoas com deficiência, moradoras de bairros com pouca informação disponível.

ODS relacionados: **ODS 10** (redução das desigualdades) e **ODS 16** (instituições eficazes e acessíveis). O módulo de zeladoria (robô RPA) contribui também, de forma complementar, para a **ODS 11** (cidades e comunidades sustentáveis).

Cidade de referência: **São José dos Campos (SP)**. As respostas vêm das páginas de serviços da Prefeitura (corpus em [03-generative-ai/corpus/fontes.csv](03-generative-ai/corpus/fontes.csv)), e o robô RPA consulta a lista pública de UBS da cidade, os avisos do Inmet e o arquivo de notícias da Prefeitura ([06-rpa/relatorio/mapa_fontes.md](06-rpa/relatorio/mapa_fontes.md)).

## Como funciona

O cidadão pergunta por voz, texto ou foto. O sistema responde com base em fontes oficiais e, se for um problema do bairro, abre um protocolo.

```
Voz, texto ou foto
   │
   ├─ Voz ─► STT ─► Motor RAG (chunking, retriever, LLM) ─► adaptação para fala ─► TTS
   ├─ Foto ─► Visão computacional (fissura em concreto, com confiança; reforça a categoria calçada)
   │
   ▼
Relato estruturado ─► confirmação do cidadão (human-in-the-loop)
   ▼
Robô RPA: valida, remove duplicados, gera protocolo, registra e notifica
   ▼
Painel Streamlit: visão do cidadão e visão do gestor, mapa e filtros
```

Módulos complementares: alerta sonoro acessível (IoT), simulação de carga em cluster e análise de computação quântica.

### Como as disciplinas se conectam

- **Perguntas (02 e 03):** o motor RAG da 03 responde às perguntas sobre serviços. Ele é usado pela aba Perguntar do app, pela rota de voz do app e pelo assistente de voz da 02. Na interface própria da 02, o assistente usa só a busca da 03 e mantém o seu LLM, a sua memória e a sua guarda de emergência. Na rota de voz do app, a 02 entra com o STT, a adaptação para fala e o TTS, e o motor completo da 03 responde. Detalhes em [02-pln-voz/README.md](02-pln-voz/README.md#como-a-voz-entra-no-app-integrado).
- **Relatos (04 e 06):** o texto passa pela máscara de dados pessoais do robô da 06 e é classificado por LLM (quando configurado), com as regras da 06 conferindo e servindo de reserva. Uma foto com fissura (04) reforça a categoria calçada. Depois da confirmação do cidadão, o protocolo é gravado no mesmo banco do robô, que também processa relatos em lote só com regras. Detalhes em [06-rpa/README.md](06-rpa/README.md#os-dois-caminhos-de-um-relato).
- **Escala (04 e 07):** a 07 simula no iSPD o classificador da 04 rodando em lote num dia de pico, e compara a hipótese de carga com a latência medida na 04 ([07-cluster/cenarios_ispd/parametros.md](07-cluster/cenarios_ispd/parametros.md)).
- **Os assuntos se cruzam:** as categorias de relato do robô (buraco, lixo, calçada, alagamento, saúde) têm página correspondente no corpus do RAG. A exceção é iluminação pública, cuja página oficial estava "em construção" e ficou fora do corpus.

## Disciplinas e entregas

| # | Disciplina | O que faz no sistema | Pasta |
|---|---|---|---|
| 1 | Front-end em Sistemas de IA | Interface Streamlit e API FastAPI, gráficos Plotly, deploy | `01-front-end` |
| 2 | PLN (Assistente de Voz) | STT, LLM, TTS, memória e adaptação para fala | `02-pln-voz` |
| 3 | Generative AI | Motor RAG: chunking, retriever, prompt e proteções | `03-generative-ai` |
| 4 | Visão Computacional | Classifica fissuras em superfícies de concreto (foto e vídeo curto); não detecta buracos | `04-visao-computacional` |
| 5 | IoT e Embedded AI | Reconhece campainha e batida na porta no celular (Edge Impulse) | `05-iot` |
| 6 | RPA e IA | Robô que transforma relatos em protocolos; máscara, classificador e banco usados também pelo app | `06-rpa` |
| 7 | Cluster Computing | Simulação no iSPD do classificador da 04 em lote, com 2 e 4 workers | `07-cluster` |
| 8 | Computação Quântica | Roadmap de otimização e criptografia pós-quântica | `08-quantica` |
| 9 | Governança em IA | Vídeo, relatório ABNT e consolidação | `09-governanca` |

Cada pasta tem um `README.md` com o checklist dos requisitos do enunciado correspondente.

## Estrutura do repositório

```
.
├── README.md
├── .env.example
├── docker-compose.yml          interface + API
├── docker/
├── docs/                       tarefas e acompanhamento (RPA, cluster e visão)
├── 01-front-end/
│   ├── api/                    FastAPI: routers, schemas, pipelines, providers
│   ├── web/                    Streamlit: features, ui, state, providers
│   └── testes/
├── 02-pln-voz/                 stt, tts, adaptacao_fala, audios_teste, testes
├── 03-generative-ai/           rag (ingestao, chunking, retriever, generator, seguranca),
│                               corpus, avaliacao, testes
├── 04-visao-computacional/     codigo, imagens, testes
├── 05-iot/                     codigo, dados_audio
├── 06-rpa/                     codigo/fluxos, dados_sinteticos, testes
├── 07-cluster/                 cenarios_ispd
├── 08-quantica/
└── 09-governanca/
```

Todas as pastas de 01 a 09 têm também `README.md` (checklist do enunciado), `evidencias/` e `relatorio/`. As pastas 01 a 06 têm `notebooks/`.

A integração acontece pela API em `01-front-end/api`, que chama os módulos das outras pastas (voz, RAG, visão e RPA). Cada módulo funciona e é avaliado sozinho.

## Como executar

```bash
cp .env.example .env      # opcional: chave do LLM. Sem ela, os relatos são classificados pelas regras do robô RPA
docker compose up --build
```

O `.env.example` vem com `LLM_PROVIDER=openai` e `gpt-4o-mini`, o LLM avaliado na 03. Nesse caso, o texto da pergunta e o texto mascarado do relato são enviados à OpenAI. Para manter tudo no computador, como escolheu a 02, use `LLM_PROVIDER=ollama` e `LLM_MODEL=qwen2.5:1.5b`.

- Interface: http://localhost:8501 (visões Cidadão e Gestor)
- API: http://localhost:8000/docs

Sem Docker, veja [01-front-end/README.md](01-front-end/README.md). Chaves de API ficam apenas no `.env`, que não é versionado.

## Proteção de dados, ética e limites

- Áudio, imagem e texto do cidadão não são guardados após o processamento, salvo o que for necessário para o protocolo e anonimizado.
- Apenas dados sintéticos ou públicos. Nenhum dado pessoal real é enviado a APIs.
- Dados pessoais (CPF, telefone, e-mail, CEP e "me chamo ...") são mascarados antes de qualquer uso do relato. A máscara não pega nome solto nem endereço completo.
- Com LLM em nuvem, o texto da pergunta e o relato já mascarado saem do computador. Com LLM local (Ollama), não saem. O áudio nunca é enviado.
- O assistente informa quando não sabe e não substitui atendimento de saúde, jurídico ou de emergência.
- A detecção de fissuras por imagem apoia a triagem de inspeções e não determina a gravidade nem a segurança estrutural.
- Toda ação final passa por confirmação humana.

Detalhes nas seções de ética de cada disciplina: [02 PLN](02-pln-voz/README.md#ética-segurança-e-lgpd), [03 Generative AI (segurança)](03-generative-ai/relatorio/relatorio_avaliacao.md#56-segurança), [04 Visão](04-visao-computacional/relatorio/relatorio_visao.md) e [06 RPA](06-rpa/README.md#proteção-de-dados-ética-e-ods).

## Links

Vídeos por disciplina (não listados no YouTube):

| Disciplina | Vídeo |
|---|---|
| 09 Governança (integração de todos os módulos) | https://youtu.be/peT0RJlUPe4 |
| 01 Front-end | https://youtu.be/3YiRxwm_ClQ |
| 02 PLN (Assistente de Voz) | https://youtu.be/RJKlXz8Ev5U |
| 03 Generative AI | https://youtu.be/P8tk_suSmPo |
| 04 Visão Computacional | https://www.youtube.com/watch?v=sOFx6vsD0AY |

Execução: não há deploy público. O sistema roda com Docker Compose (veja [Como executar](#como-executar)).
