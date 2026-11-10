# EloBairro (nome provisório)

Assistente de serviços públicos do bairro, feito para quem tem dificuldade com interfaces de texto: pessoas idosas, com baixa alfabetização, com deficiência visual, auditiva ou motora.

Projeto da Global Solution 2026.2 (FIAP, CitizenTech). Uma única solução atende nove disciplinas. Cada disciplina tem sua pasta de entrega em `entregas/`, e o código integrado fica em `src/`.

## Integrantes

| Nome completo | RM |
|---|---|
| (preencher) | (preencher) |
| (preencher) | (preencher) |
| (preencher) | (preencher) |

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
| 1 | Front-end em Sistemas de IA | Interface Streamlit e API FastAPI, gráficos Plotly, deploy | `entregas/01-front-end` |
| 2 | PLN (Assistente de Voz) | STT, LLM, TTS, memória e adaptação para fala | `entregas/02-pln-voz` |
| 3 | Generative AI | Motor RAG: chunking, retriever, prompt e proteções | `entregas/03-generative-ai` |
| 4 | Visão Computacional | Classifica fissuras e danos em fotos e vídeo curto | `entregas/04-visao-computacional` |
| 5 | IoT e Embedded AI | Reconhece campainha e batida na porta no celular (Edge Impulse) | `entregas/05-iot` |
| 6 | RPA e IA | Robô que transforma relatos em protocolos | `entregas/06-rpa` |
| 7 | Cluster Computing | Simulação no iSPD com 2 e 4 workers | `entregas/07-cluster` |
| 8 | Computação Quântica | Roadmap de otimização e criptografia pós-quântica | `entregas/08-quantica` |
| 9 | Governança em IA | Vídeo, relatório ABNT e consolidação | `entregas/09-governanca` |

Cada pasta de entrega tem um `README.md` com o checklist dos requisitos do enunciado correspondente.

## Estrutura do repositório

```
.
├── README.md
├── .env.example
├── docker-compose.yml          (a criar)
├── docs/                       problema, arquitetura, ODS, LGPD e ética
│   ├── diagramas/
│   └── evidencias/
├── src/
│   ├── api/                    back-end FastAPI
│   │   ├── routers/            endpoints
│   │   ├── schemas/            modelos Pydantic de entrada e saída
│   │   ├── pipelines/          lógica de IA
│   │   └── providers/          acesso ao LLM e a dados externos
│   ├── web/                    front-end Streamlit
│   │   ├── features/           telas por responsabilidade
│   │   ├── ui/                 componentes reutilizáveis
│   │   ├── state/              estado centralizado
│   │   └── providers/          cliente HTTP da API
│   ├── rag/                    motor RAG compartilhado
│   │   ├── ingestao/
│   │   ├── chunking/
│   │   ├── retriever/
│   │   ├── generator/
│   │   └── seguranca/          abstenção e testes de prompt injection
│   ├── voz/                    STT, TTS e adaptação do texto para fala
│   ├── visao/                  modelo e inferência de imagem e vídeo
│   ├── rpa/                    robô e fluxos
│   └── iot/                    recebimento de eventos sonoros
├── data/                       corpus, áudios e imagens de teste, dados sintéticos
├── notebooks/                  treino, avaliação e experimentos
├── tests/                      testes automatizados (pytest)
├── docker/
└── entregas/                   material específico de cada disciplina
```

O código em `src/` é único e compartilhado. As pastas de `entregas/` guardam o que cada professor avalia separadamente: relatórios, notebooks, tabelas de métricas, capturas e vídeos.

## Como executar

Será preenchido quando o código estiver pronto. Plano:

```bash
cp .env.example .env
docker compose up
```

- Interface: http://localhost:8501
- API: http://localhost:8000/docs

Chaves de API ficam apenas no `.env`, que não é versionado.

## Proteção de dados, ética e limites

- Áudio, imagem e texto do cidadão não são guardados após o processamento, salvo o que for necessário para o protocolo e anonimizado.
- Apenas dados sintéticos ou públicos. Nenhum dado pessoal real é enviado a APIs.
- O assistente informa quando não sabe e não substitui atendimento de saúde, jurídico ou de emergência.
- A detecção de danos por imagem apoia a triagem de inspeções e não determina a gravidade nem a segurança estrutural.
- Toda ação final passa por confirmação humana.

Detalhes em `docs/etica-lgpd.md`.

## Links

- Vídeo: (a preencher)
- Deploy: (a preencher)
