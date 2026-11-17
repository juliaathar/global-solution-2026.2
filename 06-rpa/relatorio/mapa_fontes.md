# Mapa de fontes públicas candidatas (coleta web)

Testado em 2026-11-16 com `curl` e leitura do HTML/XML, sem raspagem em volume. Hora e conteúdo mudam; reconferir antes de usar.
Critérios: responde, `robots.txt` permite, conteúdo no HTML/XML estático (sem JavaScript), sem dados pessoais, sem contornar CAPTCHA ou anti-bot.

Legenda: **USAR** = encaixa e foi verificada; **AVALIAR** = promissora, falta verificar; **DESCARTAR** = não usar.

## Em uso ou recomendadas
| Fonte | URL | Teste | Tema | Decisão |
|---|---|---|---|---|
| Lista de UBS, Prefeitura de SJC | `www.sjc.sp.gov.br/servicos/saude/unidades-basicas-de-saude-ubs/unidades-basicas-de-saude/` | 200, sem robots.txt (404), HTML estático, 45 UBS | BS4 + CSS + XPath | **USAR** (já implementado em `coleta_web.py`) |
| Avisos Alert-AS, Inmet (RSS) | `apiprevmet3.inmet.gov.br/avisos/rss` | 200, `application/rss+xml`, 86 avisos, robots.txt 404, licença "public domain" no feed. 37 avisos incluem "Vale do Paraíba Paulista" (região de SJC) | XPath em XML + BS4 na tabela dentro do CDATA | **USAR** (implementado em `coleta_inmet.py`): alerta de tempestade ou chuva intensa sobe a urgência de alagamento |
| Arquivo de Notícias, Prefeitura de SJC | `servicos.sjc.sp.gov.br/arquivonoticias/arquivo_noticias.aspx?pag=N` | 200, paginação `?pag=1..11` e "Próxima", 12 notícias por página, HTML estático, robots só proíbe `/sa/licitacoes/download_anexo.aspx` | Webcrawler com paginação + CSS (`div.noticia-02 h5`) + XPath (`noticia_id`) | **USAR** (implementado em `coleta_noticias.py`): crawler com limite de páginas e espera. Acervo antigo (2020 a 2024) |

Notas do feed do Inmet: cada `<item>` traz `title`, `link`, `pubDate`, `guid` e um `description` com tabela HTML em CDATA (Status, Evento, Severidade, Início, Fim, Descrição, Área, Link Gráfico). Eventos vistos: Tempestade 55, Chuvas Intensas 9, Ventos Costeiros 8, Baixa Umidade 5, Acumulado de Chuva 4, Declínio de Temperatura 4, Vendaval 1. Severidade: Perigo Potencial, Perigo, Grande Perigo. A "Área" é mesorregião, não município: o cruzamento com relatos de SJC é por "Vale do Paraíba Paulista".

Notas do Arquivo de Notícias: o filtro por secretaria e por palavra usa formulário ASP.NET (`__VIEWSTATE`) com campo de reCAPTCHA. **Não usar o formulário**; filtrar por palavra-chave no próprio robô, depois de coletar as páginas.

## A verificar
| Fonte | URL | Teste | Observação | Decisão |
|---|---|---|---|---|
| Defesa Civil de Porto Alegre, notícias | `prefeitura.poa.br/Editoria/defesa-civil?page=N` | 200, ~60 KB, paginação `?page=0..`, robots.txt não proíbe `/Editoria/` (proíbe `/node/`, `/search/`, `/admin/`...) | Conteúdo de outra cidade e com acentos que exigem cuidado de codificação (UTF-8). Serve como segunda fonte paginada, mas foge da cidade de referência | **AVALIAR** |
| Serviços de manutenção da cidade, SJC | `sjc.sp.gov.br/servicos/manutencao-da-cidade/manutencoes-diversas/` | 200, texto descritivo dos serviços (nivelamento de guias, recomposição de passeio, iluminação) | Útil para a orientação ao cidadão ("qual serviço procurar"), sem estrutura de lista | **AVALIAR** |
| Portal do Inmet | `portal.inmet.gov.br` | 200. Links: Avisos Meteorológicos (`avisos.inmet.gov.br`), Alert-AS RSS | `avisos.inmet.gov.br` devolve só 2 KB (aplicação em JavaScript): usar o RSS, não essa página | RSS: USAR; página: DESCARTAR |
| Wikipédia, São José dos Campos | `pt.wikipedia.org/wiki/São_José_dos_Campos` | 200, ~1 MB, 685 elementos de lista/tabela | Boa para treino de tabela (`table.wikitable`). Contexto, não problema do cidadão | AVALIAR (baixa prioridade) |
| Cemaden, monitoramento | `www.gov.br/cemaden/pt-br/assuntos/monitoramento` | 200, robots.txt do gov.br libera o que é público | A busca só achou boletins em PDF e notícias; não confirmei lista HTML de alertas. O Inmet cobre melhor | AVALIAR (baixa prioridade) |
| Notícias da Prefeitura de SJC (sem arquivo) | `www.sjc.sp.gov.br/noticias/` | 200, 23 links, mas `?pagina=2` devolve a mesma página | Sem paginação identificada; o arquivo é melhor | DESCARTAR |

## Descartadas
| Fonte | Motivo |
|---|---|
| `dados.prefeitura.sp.gov.br` (HTML) | `robots.txt` com `Disallow: /`. Usar API CKAN ou download seria outro tema (ingestão), não scraping |
| `defesacivil.sp.gov.br` | Proteção anti-bot (Incapsula). Contornar está fora das regras |
| `alertas2.inmet.gov.br`, `alertablu.cob.sp.gov.br` | Não responderam no teste |
| `prefeitura.sp.gov.br` | `robots.txt` devolve 403, sem permissão clara |
| Reclame Aqui e portais de notícia privados | Termos de uso e dados pessoais |
| PDFs de aviso da Defesa Civil | PDF, não HTML (BS4 não se aplica) |
| `www.sjc.sp.gov.br/servicos/saude/` e `/servicos/protecao-ao-cidadao/` | 404 |

## Como as fontes se ligam ao fluxo
1. **UBS** (já feito): relato de saúde recebe a UBS sugerida.
2. **Inmet RSS** (feito): relato de alagamento, com aviso vigente para o Vale do Paraíba, sobe a urgência e registra o aviso no relatório.
3. **Arquivo de Notícias** (feito, opcional com `RPA_USAR_NOTICIAS=1`): o crawler percorre as páginas, filtra por palavra-chave e entrega "relatos públicos" ao mesmo pipeline.

## Riscos e limites
- Sites mudam o HTML sem aviso: cada coleta tem snapshot local como caminho seguro.
- O feed do Inmet é em tempo real; para testes, guardar um snapshot (`dados_sinteticos/inmet_avisos_snapshot.xml`).
- Mesorregião não é bairro: o alerta eleva a urgência para toda a região, o que pode superestimar o risco local.
- Respeitar o `robots.txt`, usar User-Agent identificado e esperar entre requisições.
