# Relatório (PDF)

O enunciado pede um relatório em PDF com: problema e persona, ODS, arquitetura com diagrama, justificativa das escolhas, resultados das métricas, cuidados com LGPD, limitações e melhorias futuras. O esqueleto está em [relatorio.md](relatorio.md), com uma seção para cada item.

## Fluxo de trabalho

1. Rode os scripts de `testes/` (veja [../testes/README.md](../testes/README.md)). Eles gravam os resumos em `evidencias/`.
2. Preencha os marcadores `[PREENCHER: ...]` do `relatorio.md`. Escreva a análise dos números e a conclusão com as palavras do grupo.
3. Monte o relatório com as tabelas reais:
   ```bash
   python relatorio/montar.py --sem-instrucoes
   ```
   O script cria `relatorio_montado.md` (não versionado), troca cada `<!-- INCLUIR: evidencias/... -->` pelo resumo correspondente, e informa quantas pendências restam e quais evidências ainda faltam.
4. O diagrama já está em `figuras/arquitetura.png` (para refazer: `pip install matplotlib` e `python relatorio/gerar_diagrama.py`). Gere o PDF com `pip install markdown weasyprint` e `python relatorio/gerar_pdf.py`: ele monta o relatório, troca os marcadores pelas tabelas e salva `relatorio/relatorio_pln_voz.pdf`. Ele **recusa** gerar a versão final enquanto houver `[PREENCHER]` ou evidência faltando; `--rascunho` gera `relatorio_rascunho.pdf` (não versionado) para ver o layout.

Antes de entregar, confira que `python relatorio/montar.py --sem-instrucoes` informa **0 pendências** e nenhuma evidência faltando.
