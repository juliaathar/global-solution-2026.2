import markdown, re, pathlib, subprocess, sys
d = pathlib.Path(sys.argv[1])
md = (d/"relatorio_quantica.md").read_text(encoding="utf-8")
md = re.sub(r"^---\n.*?\n---\n", "", md, flags=re.S)
body = markdown.markdown(md, extensions=["tables"])
body = re.sub(r'(https?://[^\s<]+)', r'<a href="\1">\1</a>', body)
css = """
@page{size:A4;margin:18mm 16mm}
body{font-family:'Atkinson Hyperlegible','Segoe UI',Arial,sans-serif;color:#17283A;font-size:10.5pt;line-height:1.5;max-width:780px;margin:auto}
h1{color:#0E6A8A;font-size:22pt;margin:0 0 4px;border-bottom:4px solid #F2B705;padding-bottom:6px}
h2{color:#0E6A8A;font-size:14pt;margin-top:22px;break-after:avoid}
h3{font-size:11.5pt;margin-top:16px;break-after:avoid}
table{border-collapse:collapse;width:100%;margin:8px 0;font-size:9.5pt;break-inside:avoid}
th{background:#0E6A8A;color:#fff;text-align:left}
th,td{border:1px solid #c9d3dc;padding:5px 7px;vertical-align:top}
tr:nth-child(even) td{background:#F3F6F9}
hr{border:0;border-top:1px solid #c9d3dc;margin:18px 0}
a{color:#0E6A8A;word-break:break-all}
"""
html = f'<!DOCTYPE html><html lang="pt-BR"><head><meta charset="utf-8"><title>EloBairro e a computação quântica</title><style>{css}</style></head><body>{body}</body></html>'
(d/"relatorio_quantica.html").write_text(html, encoding="utf-8")
subprocess.run(["google-chrome","--headless","--no-sandbox","--disable-gpu",f"--print-to-pdf={d/'relatorio_quantica.pdf'}","--no-pdf-header-footer",str((d/'relatorio_quantica.html').resolve())],check=True,capture_output=True)
