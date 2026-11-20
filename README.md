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

ODS relacionados: **ODS 10** (redução das desigualdades) e **ODS 16** (instituições eficazes e acessíveis).

> Fontes que sustentam a dor do problema (dados, notícias, relatos) serão listadas em `docs/problema-publico.md`.

## Como funciona

O cidadão pergunta por voz, texto ou foto. O sistema responde com base em fontes oficiais e, se for um problema do bairro, abre um protocolo.

```
Voz, texto ou foto
   │
   ├─ Voz ─► STT ─► Motor RAG (chunking, retriever, LLM) ─► adaptação para fala ─► TTS
   ├─ Foto ─► Visão computacional (dano ou fissura, com confiança)
   │
   ▼
Relato estruturado ─► confirmação do cidadão (human-in-the-loop)
   ▼
Robô RPA: valida, remove duplicados, gera protocolo, registra e notifica
   ▼
Painel Streamlit: visão do cidadão e visão do gestor, mapa e filtros
```

Módulos complementares: alerta sonoro acessível (IoT), simulação de carga em cluster e análise de computação quântica.

## Disciplinas e entregas

| # | Disciplina | O que faz no sistema | Pasta |
|---|---|---|---|
| 1 | Front-end em Sistemas de IA | Interface Streamlit e API FastAPI, gráficos Plotly, deploy | `01-front-end` |
| 2 | PLN (Assistente de Voz) | STT, LLM, TTS, memória e adaptação para fala | `02-pln-voz` |
| 3 | Generative AI | Motor RAG: chunking, retriever, prompt e proteções | `03-generative-ai` |
| 4 | Visão Computacional | Classifica fissuras e danos em fotos e vídeo curto | `04-visao-computacional` |
| 5 | IoT e Embedded AI | Reconhece campainha e batida na porta no celular (Edge Impulse) | `05-iot` |
| 6 | RPA e IA | Robô que transforma relatos em protocolos | `06-rpa` |
| 7 | Cluster Computing | Simulação no iSPD com 2 e 4 workers | `07-cluster` |
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
├── docs/                       problema, arquitetura, ODS, LGPD e ética
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

- Interface: http://localhost:8501 (visões Cidadão e Gestor)
- API: http://localhost:8000/docs

Sem Docker, veja [01-front-end/README.md](01-front-end/README.md). Chaves de API ficam apenas no `.env`, que não é versionado.

## Proteção de dados, ética e limites

- Áudio, imagem e texto do cidadão não são guardados após o processamento, salvo o que for necessário para o protocolo e anonimizado.
- Apenas dados sintéticos ou públicos. Nenhum dado pessoal real é enviado a APIs.
- O assistente informa quando não sabe e não substitui atendimento de saúde, jurídico ou de emergência.
- A detecção de danos por imagem apoia a triagem de inspeções e não determina a gravidade nem a segurança estrutural.
- Toda ação final passa por confirmação humana.

Detalhes em `docs/etica-lgpd.md`.

## Links

- Vídeo de Governança (integração de todos os módulos): https://youtu.be/peT0RJlUPe4
- Vídeo de Front-end: https://youtu.be/3YiRxwm_ClQ
- Vídeo de PLN (assistente de voz): https://youtu.be/RJKlXz8Ev5U
- Vídeo de Generative AI (RAG): https://youtu.be/P8tk_suSmPo
- Vídeo de Visão Computacional: https://www.youtube.com/watch?v=sOFx6vsD0AY
- Execução: local, com `docker compose up` (sem deploy público)
