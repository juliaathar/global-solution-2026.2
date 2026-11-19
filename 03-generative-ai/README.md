# 03 Generative AI: Assistente Conversacional

Projeto **EloBairro**, disciplina Generative AI & Advanced Nets (Turma 2TIAPF), Global Solution 2026.2.

**Integrantes:**

| Nome completo | RM |
|---|---|
| Bruno Fernandes Nascimento | 552574 |
| Edgar Lódula de Assis | 565260 |
| Júlia Aben-Athar | 566325 |

## Checklist
- [x] Corpus identificável: fontes, URLs, datas de consulta
- [x] Chunking justificado (tamanho, overlap, metadados), comparando configurações
- [x] Retriever justificado (BM25, denso ou híbrido; embeddings, top-k, filtros, reranking)
- [x] Generator justificado (LLM, prompt, parâmetros, citação de fontes, abstenção)
- [~] Pipeline funcional integrado ao protótipo (`POST /rag/perguntar` montado em `01-front-end/api/main.py` e testado; rodar de `01-front-end`: `uvicorn api.main:app --port 8000`)
- [x] Mínimo de 10 perguntas: respondíveis, sem resposta, ambíguas, desvio de propósito
- [x] Avaliação separada: recuperação, geração (contexto controlado), sistema completo
- [x] Proteção contra resposta não sustentada
- [x] 2+ testes adversariais (prompt injection, vazamento de prompt ou dados)
- [x] Sem credenciais nem dados pessoais expostos
- [~] Relatório: perguntas, evidências recuperadas, respostas, métricas, análise crítica (`relatorio/relatorio_avaliacao.md`; a seção 6.4 traz a revisão humana de 15 respostas, feita por Júlia Aben-Athar; exportar para PDF se exigido)
- [x] Vídeo de até 5 min com sucessos, falhas, mitigação e limites: https://youtu.be/P8tk_suSmPo (não listado; roteiro em `relatorio/roteiro_video.md`)

## Corpus e ingestão

- Município: São José dos Campos (mesma cidade do RPA em `06-rpa`). Fonte: páginas de serviços do portal da Prefeitura (`sjc.sp.gov.br/servicos/`).
- `corpus/fontes_entrada.csv`: 36 URLs escolhidas (zeladoria, saúde, assistência social, mobilidade acessível).
- `corpus/fontes.csv`: resultado por fonte (URL, data de consulta, título, status, tamanho, hash).
- `corpus/documentos.jsonl`: 33 documentos limpos (cerca de 91 mil caracteres), com `id`, `url`, `titulo`, `categoria`, `data_consulta`, `texto`. Títulos de seção ficam como linhas `## ...` para o chunking por estrutura.
- `corpus/bruto/`: HTML original, para reproduzir sem depender do site.

Como executar (a partir de `03-generative-ai`):

```bash
pip install -r requirements.txt
python rag/ingestao/ingestao.py            # baixa, limpa e grava o corpus
python rag/ingestao/ingestao.py --offline  # reaproveita o HTML de corpus/bruto
```

Limites conhecidos do corpus:
- A página `cartao-de-estacionamento-do-idoso` foi removida: o HTML trazia só os termos de uso do portal, não o serviço (achado na montagem do conjunto de perguntas).
- 3 páginas descartadas por texto curto: iluminação pública ("em construção"), consulta de exames e guia rebaixada (conteúdo só em PDF).
- Várias páginas são índices de cartões ou apontam para PDFs; o conteúdo dos PDFs não está no corpus.
- `tapa-buracos` traz uma programação semanal que fica desatualizada em dias; a resposta deve citar a data de consulta.
- Robots.txt do site não existe (404); a coleta usa User-Agent identificado e espera de 1,5 s entre páginas.

## Decisões técnicas e resultados

| Componente | Escolha | Por quê (evidência) |
|---|---|---|
| Chunking | por seção (títulos `## ...`, máx. 1200 caracteres), com o título da página no início de cada trecho | com e5-large, evidência no top-1 em 95% (dev) e 5 de 9 (validação); `evidencias/retrievers_analise.md` |
| Retriever | vetorial, `intfloat/multilingual-e5-large` (fastembed, CPU), top-3 | BM25 falha com sinônimos e plurais; híbrido por RRF não superou o vetorial puro; ~100 ms por consulta |
| Generator | `gpt-4o-mini`, temperatura 0,1, 400 tokens, prompt com papel, 8 regras, citação `[n]` e abstenção | 29 de 30 respondíveis corretas (1 falsa abstenção) e 100% de abstenção nas sem resposta; `evidencias/sistema_analise.md` |
| Abstenção | cosseno do melhor trecho < 0,84, e regra de abstenção no prompt | margem estreita (~0,01); só o limiar não basta, só o prompt também não: camadas se complementam |
| Segurança | filtro de entrada, neutralização de contexto, prompt, abstenção | 0 de 9 ataques diretos e 0 de 4 injeções indiretas funcionaram; as regras são frágeis e a resistência vem do modelo; `evidencias/seguranca_analise.md` |

Como reproduzir as avaliações (a partir de `03-generative-ai`, com o `.env` na raiz do repo):

```bash
python avaliacao/avaliar_recuperacao.py   # BM25 por chunking
python avaliacao/avaliar_retrievers.py    # BM25, vetorial e híbrido (baixa o e5-large, ~2,2 GB)
python avaliacao/validar_limiar.py        # limiar em perguntas novas
python avaliacao/avaliar_sistema.py       # geração e sistema completo (usa a API)
python avaliacao/avaliar_seguranca.py     # testes adversariais (usa a API)
```

Uso do motor:

```python
from rag.motor import responder
r = responder("Quais documentos preciso para o Cadastro Único?", historico=[])
r["resposta"], r["fontes"], r["abstencao"]
```

Testes automáticos (23, sem rede): `python -m unittest discover -s testes -v`. Os 2 de `test_api_rag.py` montam o app principal do `01-front-end`, que importa o módulo de visão; para rodá-los instale também `../01-front-end/requirements.txt` (inclui `torch`).

Entregáveis e pendências:
- `relatorio/relatorio_avaliacao.md`: relatório de avaliação (seções 1 a 8 e anexos).
- `relatorio/revisao_humana_amostra.md`: ficha com as 15 respostas revisadas por Júlia Aben-Athar; o resultado está na seção 6.4 do relatório.
- `relatorio/roteiro_video.md`: roteiro de 4 min 40 s para o vídeo.
- Vídeo gravado e publicado como não listado no YouTube: https://youtu.be/P8tk_suSmPo. Nome e RM constam neste README e no relatório; o router do RAG já está montado em `01-front-end/api/main.py`.
