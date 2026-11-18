"""Gera relatorio_cluster.pdf a partir de relatorio_cluster.html (fonte do relatório).

Uso: pip install weasyprint && python gerar_pdf.py
"""
from pathlib import Path

from weasyprint import HTML

AQUI = Path(__file__).resolve().parent
HTML(filename=str(AQUI / "relatorio_cluster.html")).write_pdf(str(AQUI / "relatorio_cluster.pdf"))
print("Gerado:", AQUI / "relatorio_cluster.pdf")
