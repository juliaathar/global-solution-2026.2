"""Calcula acerto, matriz de confusão e falsos positivos a partir das planilhas preenchidas pelo grupo.

Duas avaliações, cada uma numa planilha CSV em evidencias/:

  model_testing.csv       Model testing (Classify all) nos 5 arquivos de Test por classe.
                          Colunas: arquivo, real, previsto, confianca
  tentativas_ao_vivo.csv  15 tentativas ao vivo no celular (Run this model), 5 por classe.
                          Colunas: tentativa, som_tocado, real, previsto, confianca, observacao

Uso:
    python avaliar.py modelos      # cria as duas planilhas em branco (model_testing a partir do manifesto)
    python avaliar.py modelo       # lê model_testing.csv e gera resultado_model_testing.md + matriz PNG
    python avaliar.py ao-vivo      # lê tentativas_ao_vivo.csv e gera resultado_ao_vivo.md + matriz PNG

"previsto" aceita: campainha, batida_porta, ambiente ou incerto (quando o Edge Impulse mostra "uncertain").
"""
import argparse
import csv
import sys
from datetime import datetime

from comum import CLASSES, EVIDENCIAS, MANIFESTO

PREVISTOS = (*CLASSES, "incerto")
NOMES = {"campainha": "Campainha", "batida_porta": "Batida na porta", "ambiente": "Ambiente", "incerto": "Incerto"}
SONS_SUGERIDOS = {
    "campainha": ["campainha da casa", "campainha de outra casa / vídeo", "campainha com TV ligada",
                  "campainha a 3 m do celular", "campainha com conversa ao fundo"],
    "batida_porta": ["3 batidas com os nós dos dedos", "batida forte com a mão", "batida fraca",
                     "batida em porta de outro material", "batida com rádio ligado"],
    "ambiente": ["conversa normal", "TV ou música", "panela / louça na cozinha",
                 "porta de armário fechando", "silêncio da sala"],
}


def ler(arquivo: str) -> list[dict]:
    caminho = EVIDENCIAS / arquivo
    if not caminho.exists():
        sys.exit(f"{caminho} não existe. Rode: python avaliar.py modelos")
    with open(caminho, encoding="utf-8") as f:
        linhas = [l for l in csv.DictReader(f) if (l.get("previsto") or "").strip()]
    for l in linhas:
        l["real"], l["previsto"] = l["real"].strip().lower(), l["previsto"].strip().lower()
        if l["real"] not in CLASSES or l["previsto"] not in PREVISTOS:
            sys.exit(f"Valor inválido na linha {l}: use {', '.join(PREVISTOS)}")
    if not linhas:
        sys.exit(f"{arquivo} ainda não tem a coluna 'previsto' preenchida.")
    return linhas


def matriz(linhas: list[dict]) -> dict:
    m = {r: {p: 0 for p in PREVISTOS} for r in CLASSES}
    for l in linhas:
        m[l["real"]][l["previsto"]] += 1
    return m


def figura(m: dict, titulo: str, arquivo: str) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    cols = [p for p in PREVISTOS if p != "incerto" or any(m[r]["incerto"] for r in CLASSES)]
    dados = [[m[r][p] for p in cols] for r in CLASSES]
    fig, ax = plt.subplots(figsize=(6.2, 4.6))
    ax.imshow(dados, cmap="Blues")
    for i, linha in enumerate(dados):
        for j, v in enumerate(linha):
            ax.text(j, i, v, ha="center", va="center", fontsize=14,
                    color="white" if v > max(map(max, dados)) / 2 else "black")
    ax.set_xticks(range(len(cols)), [NOMES[c] for c in cols])
    ax.set_yticks(range(len(CLASSES)), [NOMES[c] for c in CLASSES])
    ax.set_xlabel("Previsto pelo modelo")
    ax.set_ylabel("Som real")
    ax.set_title(titulo)
    fig.tight_layout()
    fig.savefig(EVIDENCIAS / arquivo, dpi=150)
    plt.close(fig)


def relatorio(linhas: list[dict], titulo: str, base: str, detalhe: bool) -> None:
    m = matriz(linhas)
    acertos = sum(l["real"] == l["previsto"] for l in linhas)
    total = len(linhas)
    por_classe = {c: (m[c][c], sum(m[c].values())) for c in CLASSES}
    fp_ambiente = [l for l in linhas if l["real"] == "ambiente" and l["previsto"] in ("campainha", "batida_porta")]
    perdidos = [l for l in linhas if l["real"] != "ambiente" and l["previsto"] in ("ambiente", "incerto")]
    figura(m, titulo, f"{base}_matriz.png")
    md = [f"# {titulo}", "", f"Gerado por `codigo/avaliar.py` em {datetime.now():%d/%m/%Y %H:%M}.", "",
          f"**Acerto geral: {acertos} de {total} ({100 * acertos / total:.1f}%)**", "",
          "| Classe | Acertos | Total | % |", "|---|---|---|---|"]
    md += [f"| {NOMES[c]} | {a} | {t} | {100 * a / t:.0f}% |" if t else f"| {NOMES[c]} | 0 | 0 | - |"
           for c, (a, t) in por_classe.items()]
    md += ["", f"![Matriz de confusão]({base}_matriz.png)", "", "## Matriz de confusão", "",
           "| Real \\ Previsto | " + " | ".join(NOMES[p] for p in PREVISTOS) + " |",
           "|---|" + "---|" * len(PREVISTOS)]
    md += [f"| {NOMES[r]} | " + " | ".join(str(m[r][p]) for p in PREVISTOS) + " |" for r in CLASSES]
    md += ["", "## Falsos positivos na classe ambiente (som comum que viraria alerta)", ""]
    md += [f"- {l.get('som_tocado') or l.get('arquivo')}: previsto **{NOMES[l['previsto']]}** "
           f"({l.get('confianca', '')})" for l in fp_ambiente] or ["- Nenhum."]
    md += ["", "## Campainha ou batida que não virou alerta", ""]
    md += [f"- {l.get('som_tocado') or l.get('arquivo')}: previsto **{NOMES[l['previsto']]}**" for l in perdidos] or ["- Nenhuma."]
    if detalhe:
        md += ["", "## Tentativas", "", "| # | Som tocado | Real | Previsto | Confiança | Acertou? | Observação |",
               "|---|---|---|---|---|---|---|"]
        md += [f"| {l.get('tentativa', i + 1)} | {l.get('som_tocado', '')} | {NOMES[l['real']]} | {NOMES[l['previsto']]} | "
               f"{l.get('confianca', '')} | {'✅' if l['real'] == l['previsto'] else '❌'} | {l.get('observacao', '')} |"
               for i, l in enumerate(linhas)]
    (EVIDENCIAS / f"{base}.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print("\n".join(md[:12 + len(CLASSES)]))
    print(f"\nGravado em evidencias/{base}.md e evidencias/{base}_matriz.png")


def criar_modelos() -> None:
    EVIDENCIAS.mkdir(exist_ok=True)
    vivo = EVIDENCIAS / "tentativas_ao_vivo.csv"
    if not vivo.exists():
        with open(vivo, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["tentativa", "som_tocado", "real", "previsto", "confianca", "observacao"])
            n = 1
            for c in CLASSES:
                for som in SONS_SUGERIDOS[c]:
                    w.writerow([n, som, c, "", "", ""])
                    n += 1
        print(f"Criado {vivo}")
    modelo = EVIDENCIAS / "model_testing.csv"
    if not modelo.exists():
        testes = []
        if MANIFESTO.exists():
            with open(MANIFESTO, encoding="utf-8") as f:
                testes = [l for l in csv.DictReader(f) if l["conjunto"] == "testing"]
        with open(modelo, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["arquivo", "real", "previsto", "confianca"])
            for l in testes:
                w.writerow([l["arquivo"].split("/")[-1], l["classe"], "", ""])
            if not testes:  # gravou direto no Edge Impulse: 5 linhas por classe para colar o nome da amostra
                for c in CLASSES:
                    for i in range(1, 6):
                        w.writerow([f"(nome no Edge Impulse) {c} {i}", c, "", ""])
        print(f"Criado {modelo}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("acao", choices=["modelos", "modelo", "ao-vivo"])
    a = ap.parse_args().acao
    if a == "modelos":
        criar_modelos()
    elif a == "modelo":
        relatorio(ler("model_testing.csv"), "Model testing (5 arquivos de Test por classe)", "resultado_model_testing", False)
    else:
        relatorio(ler("tentativas_ao_vivo.csv"), "Teste ao vivo no celular (15 tentativas)", "resultado_ao_vivo", True)


if __name__ == "__main__":
    main()
