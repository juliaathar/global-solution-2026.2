"""Gera o relatório em PDF a partir de relatorio.md (com as tabelas de evidencias/ e o diagrama).

    python relatorio/gerar_pdf.py              # versão final: só gera se não houver pendências
    python relatorio/gerar_pdf.py --rascunho   # gera relatorio_rascunho.pdf mesmo com pendências

Dependências: pip install markdown weasyprint. O diagrama vem de `python relatorio/gerar_diagrama.py`.
A versão final (relatorio_pln_voz.pdf) só sai com 0 marcadores [PREENCHER] e todas as evidências presentes.
"""
import argparse
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parent
sys.path.insert(0, str(AQUI))
from montar import montar  # noqa: E402

CSS = """
@page { size: A4; margin: 18mm; @bottom-center { content: counter(page) " / " counter(pages); font-size: 8pt; color: #777; } }
body { font-family: "DejaVu Sans", Arial, sans-serif; font-size: 9.5pt; line-height: 1.4; color: #111; }
h1 { font-size: 19pt; margin: 0 0 6pt; } h2 { font-size: 13pt; margin: 16pt 0 4pt; color: #1b3a6b; }
h3 { font-size: 11pt; margin: 12pt 0 3pt; } h4 { font-size: 10pt; margin: 8pt 0 2pt; }
table { border-collapse: collapse; width: 100%; margin: 6pt 0 8pt; font-size: 8.3pt; }
th, td { border: 1px solid #999; padding: 3pt 5pt; text-align: left; vertical-align: top; }
th { background: #e8edf5; } tr { break-inside: avoid; }
img { max-width: 100%; } code { font-family: "DejaVu Sans Mono", monospace; font-size: 8.3pt; background: #f2f2f2; }
pre { background: #f2f2f2; padding: 5pt; font-size: 8pt; white-space: pre-wrap; } blockquote { color: #444; border-left: 3px solid #ccc; margin-left: 0; padding-left: 8pt; }
a { color: #1b3a6b; word-break: break-all; }
"""


def gerar(rascunho: bool) -> int:
    import markdown
    from weasyprint import HTML
    texto, faltando, pendencias = montar((AQUI / "relatorio.md").read_text(encoding="utf-8"), RAIZ, sem_instrucoes=True)
    if not rascunho and (pendencias or faltando):
        print(f"Não gerei a versão final: {pendencias} marcadores [PREENCHER] e {len(faltando)} evidências faltando.")
        for f in faltando:
            print("  falta:", f)
        print("Rode com --rascunho para ver o layout com as pendências.")
        return 1
    if not (AQUI / "figuras" / "arquitetura.png").is_file():
        print("Falta relatorio/figuras/arquitetura.png: rode python relatorio/gerar_diagrama.py")
        return 1
    corpo = markdown.markdown(texto, extensions=["tables", "fenced_code", "sane_lists"])
    aviso = ('<p style="background:#fff3cd;border:1px solid #e0b000;padding:4pt"><b>RASCUNHO</b>: '
             f'{pendencias} pendências e {len(faltando)} evidências faltando.</p>') if rascunho else ""
    html = f'<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><title>Assistente de Voz do EloBairro</title><style>{CSS}</style></head><body>{aviso}{corpo}</body></html>'
    destino = AQUI / ("relatorio_rascunho.pdf" if rascunho else "relatorio_pln_voz.pdf")
    HTML(string=html, base_url=str(AQUI)).write_pdf(str(destino))
    print("Gerado:", destino, f"({pendencias} pendências, {len(faltando)} evidências faltando)")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--rascunho", action="store_true")
    sys.exit(gerar(ap.parse_args().rascunho))
