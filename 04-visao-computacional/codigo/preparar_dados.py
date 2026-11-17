"""Etapa 1: amostra os dados e separa treino/validação/teste sem vazamento.

O dataset foi gerado recortando ~458 imagens grandes e não informa a origem de cada recorte.
Como arquivos com numeração próxima tendem a vir da mesma imagem original, a separação é
feita por BLOCOS de arquivos consecutivos: um bloco inteiro vai para um único conjunto.
Limitação: é uma aproximação, não uma garantia. Declarar isso no relatório.
"""
import csv
import random

import config


def listar(pasta):
    return sorted(p for p in pasta.iterdir() if p.suffix.lower() in {".jpg", ".jpeg", ".png"})


def main():
    rnd = random.Random(config.SEMENTE)
    linhas = []
    for nome_pasta, rotulo in config.PASTAS.items():
        pasta = config.IMAGENS / nome_pasta
        if not pasta.exists():
            raise SystemExit(f"Pasta não encontrada: {pasta}. Baixe o dataset (ver config.py).")
        arquivos = listar(pasta)
        blocos = [arquivos[i:i + config.TAMANHO_BLOCO] for i in range(0, len(arquivos), config.TAMANHO_BLOCO)]
        rnd.shuffle(blocos)
        escolhidos, total = [], 0
        for b in blocos:  # amostra por blocos inteiros até atingir a quantidade
            if total >= config.AMOSTRA_POR_CLASSE:
                break
            escolhidos.append(b)
            total += len(b)
        n = len(escolhidos)
        corte1 = round(n * config.PROPORCOES[0])
        corte2 = corte1 + round(n * config.PROPORCOES[1])
        for i, bloco in enumerate(escolhidos):
            conjunto = "treino" if i < corte1 else "validacao" if i < corte2 else "teste"
            for arq in bloco:
                linhas.append({"arquivo": str(arq), "rotulo": rotulo, "conjunto": conjunto, "bloco": f"{nome_pasta}-{i}"})
    config.SAIDA.mkdir(parents=True, exist_ok=True)
    with open(config.MANIFESTO, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["arquivo", "rotulo", "conjunto", "bloco"])
        w.writeheader()
        w.writerows(linhas)
    for c in ("treino", "validacao", "teste"):
        print(c, sum(1 for l in linhas if l["conjunto"] == c))
    # checagem de vazamento: nenhum bloco em mais de um conjunto
    por_bloco = {}
    for l in linhas:
        por_bloco.setdefault(l["bloco"], set()).add(l["conjunto"])
    assert all(len(v) == 1 for v in por_bloco.values()), "vazamento entre conjuntos"
    print("Manifesto salvo em", config.MANIFESTO)


if __name__ == "__main__":
    main()
