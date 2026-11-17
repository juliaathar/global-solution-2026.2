"""Compara o classificador por regras com um modelo de ML (TF-IDF + regressão logística) e com um híbrido.

Treino: só os dados sintéticos (dados_sinteticos/relatos.csv). Avaliação: a amostra independente de 60 relatos
escritos à mão, separada em desenvolvimento e teste. O modelo nunca vê a amostra independente.

Híbrido: usa as regras; se elas devolverem "indefinido" (sem palavra conhecida), pergunta ao modelo e só aceita a
resposta se a probabilidade for >= LIMIAR. Abaixo disso o relato segue para revisão humana.

Uso: python avaliar_ml.py [--amostra caminho.csv]   (precisa de scikit-learn: pip install scikit-learn)
"""
import argparse
import csv
import sys

import config
from classificador import classificar
from deduplicacao import normalizar

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import make_pipeline
except ImportError:
    sys.exit("Instale o scikit-learn: pip install scikit-learn")

LIMIAR = 0.5


def carregar_treino():
    linhas = list(csv.DictReader(open(config.ENTRADA, encoding="utf-8")))
    return [(normalizar(r["texto"]), r["categoria_real"], r["urgencia_real"]) for r in linhas
            if r["categoria_real"] and r["texto"].strip()]


def treinar(treino):
    X = [t for t, _, _ in treino]
    modelo_cat = make_pipeline(TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True), LogisticRegression(max_iter=1000))
    modelo_urg = make_pipeline(TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True), LogisticRegression(max_iter=1000))
    modelo_cat.fit(X, [c for _, c, _ in treino])
    modelo_urg.fit(X, [u for _, _, u in treino])
    return modelo_cat, modelo_urg


def prever_ml(modelos, texto):
    mc, mu = modelos
    t = [normalizar(texto)]
    p = mc.predict_proba(t)[0]
    i = p.argmax()
    return {"categoria": mc.classes_[i], "urgencia": mu.predict(t)[0], "confianca": float(p[i])}


def prever_hibrido(modelos, texto):
    r = classificar(texto)
    if r["categoria"] != "indefinido":
        return r
    m = prever_ml(modelos, texto)
    return m if m["confianca"] >= LIMIAR else r


def medir(linhas, prever):
    n = len(linhas)
    cat = urg = revisao = 0
    for r in linhas:
        p = prever(r["texto"])
        cat += p["categoria"] == r["categoria_real"]
        urg += p["urgencia"] == r["urgencia_real"]
        revisao += p["categoria"] == "indefinido" or p["confianca"] < config.CONFIANCA_MINIMA
    return n, cat, urg, revisao


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--amostra", default=str(config.RAIZ / "dados_sinteticos" / "amostra_independente.csv"))
    args = ap.parse_args()
    amostra = list(csv.DictReader(open(args.amostra, encoding="utf-8")))
    treino = carregar_treino()
    modelos = treinar(treino)
    print(f"Treino: {len(treino)} relatos sintéticos | Avaliação: {len(amostra)} relatos escritos à mão")
    metodos = {"regras": classificar, "ML (TF-IDF + regressão logística)": lambda t: prever_ml(modelos, t),
               f"híbrido (regras, ML se 'indefinido' e prob >= {LIMIAR})": lambda t: prever_hibrido(modelos, t)}
    for grupo in ("desenvolvimento", "teste", "todos"):
        sub = [r for r in amostra if grupo == "todos" or r.get("grupo") == grupo]
        if not sub:
            continue
        print(f"\n[{grupo}] {len(sub)} relatos")
        for nome, fn in metodos.items():
            n, cat, urg, rev = medir(sub, fn)
            print(f"  {nome:<58} categoria {cat / n:6.1%} | urgência {urg / n:6.1%} | revisão humana {rev}/{n}")

    # Variante: acrescenta ao treino os relatos escritos à mão do grupo de desenvolvimento e mede só no teste
    dev = [(normalizar(r["texto"]), r["categoria_real"], r["urgencia_real"]) for r in amostra if r.get("grupo") == "desenvolvimento"]
    teste = [r for r in amostra if r.get("grupo") == "teste"]
    if dev and teste:
        modelos2 = treinar(treino + dev)
        print(f"\n[teste, modelo treinado com sintéticos + {len(dev)} relatos de desenvolvimento] {len(teste)} relatos")
        for nome, fn in {"ML": lambda t: prever_ml(modelos2, t),
                         "híbrido": lambda t: prever_hibrido(modelos2, t)}.items():
            n, cat, urg, rev = medir(teste, fn)
            print(f"  {nome:<58} categoria {cat / n:6.1%} | urgência {urg / n:6.1%} | revisão humana {rev}/{n}")
