set -e
node gerar_chaves.js
for i in 1 2 3; do node gerar.js >/dev/null; soffice --headless --convert-to pdf relatorio_governanca.docx >/dev/null 2>&1; python3 paginas.py relatorio_governanca.pdf; done
pdftotext relatorio_governanca.pdf texto.txt
