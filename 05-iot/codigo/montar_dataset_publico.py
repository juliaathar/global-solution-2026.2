"""Monta o dataset do OuviAí a partir de sons públicos (usado no lugar de gravações próprias).

- batida_porta: clipes "door_wood_knock" do ESC-50 (Piczak, 2015; CC BY-NC 3.0).
- ambiente: clipes de sons domésticos do ESC-50 (passos, teclado, relógio, porta rangendo, máquina de lavar).
- campainha: gravações reais de campainhas e avisos sonoros domésticos do dataset Visualfy (Zenodo 3689288,
  CC BY 4.0). O Visualfy numera os aparelhos (pattern_01 a pattern_24) sem dizer o que é cada um; usamos os
  que têm assinatura de campainha no espectrograma ("ding-dong" de dois tons e toque de sino com decaimento).
- ambiente: além do ESC-50, sons indesejados do Visualfy (porta batendo, panelas, música, água, palmas, tosse,
  passos), que são justamente os que mais confundem com campainha e batida.

Para cada classe são 20 clipes de 5 s para o dataset e 5 clipes DIFERENTES (outras gravações de origem)
para o teste ao vivo, que são tocados no alto-falante do computador perto do celular.

Uso:  python montar_dataset_publico.py --esc50 <pasta do ESC-50> --visualfy <pasta few_shot_vfy_zenodo>
Saída: dados_audio/brutos/<classe>/ (depois rode preparar_audios.py) e dados_audio/teste_ao_vivo/
"""
import argparse
import csv
import random
import shutil
from pathlib import Path

from comum import BRUTOS, DADOS

AO_VIVO = DADOS / "teste_ao_vivo"
CLASSES_AMBIENTE_DATASET = ["footsteps", "keyboard_typing", "clock_tick", "door_wood_creaks", "washing_machine"]
CLASSES_AMBIENTE_AO_VIVO = ["mouse_click", "can_opening", "vacuum_cleaner"]
# Visualfy: aparelhos com assinatura de campainha (inspeção dos espectrogramas)
CAMPAINHA_DATASET = ["pattern_01", "pattern_02", "pattern_18", "pattern_19", "pattern_22"]  # 4 clipes de cada
CAMPAINHA_AO_VIVO = [("pattern_20", 3), ("pattern_01", 1), ("pattern_18", 1)]  # pattern_20 nunca aparece no treino
INDESEJADOS_DATASET = ["door_slam", "pots_and_pans", "music", "water", "clapping"]  # 2 de cada
INDESEJADOS_AO_VIVO = ["cough", "steps"]
def selecionar(meta: Path, semente: int = 42) -> dict:
    linhas = list(csv.DictReader(open(meta, encoding="utf-8")))
    rnd, usados = random.Random(semente), set()

    def pegar(cat, n):
        cands = [x for x in linhas if x["category"] == cat and x["src_file"] not in usados]
        rnd.shuffle(cands)
        out = []
        for x in cands:  # uma gravação de origem nunca aparece em dois conjuntos
            if x["src_file"] not in usados:
                out.append(x)
                usados.add(x["src_file"])
            if len(out) == n:
                return out
        raise ValueError(f"{cat}: só {len(out)} clipes")

    sel = {"batida_porta": {"dataset": pegar("door_wood_knock", 20), "ao_vivo": pegar("door_wood_knock", 5)}}
    sel["ambiente"] = {"dataset": [x for c in CLASSES_AMBIENTE_DATASET for x in pegar(c, 2)],
                       "ao_vivo": [x for c in CLASSES_AMBIENTE_AO_VIVO for x in pegar(c, 1)]}
    return sel


def selecionar_visualfy(raiz: Path, semente: int = 7) -> dict:
    """Clipes diferentes para dataset e teste ao vivo; caminhos relativos à pasta few_shot_vfy_zenodo."""
    rnd = random.Random(semente)
    clipes = {}

    def lista(sub):
        if sub not in clipes:
            arqs = sorted((raiz / sub).glob("*.wav"))
            rnd.shuffle(arqs)
            clipes[sub] = arqs
        return clipes[sub]

    camp_ds = [a for p in CAMPAINHA_DATASET for a in lista(f"pattern_sounds/{p}")[:4]]
    camp_vivo = [a for p, n in CAMPAINHA_AO_VIVO for a in lista(f"pattern_sounds/{p}")[10:10 + n]]
    amb_ds = [a for c in INDESEJADOS_DATASET for a in lista(f"unwanted_sounds/{c}")[:2]]
    amb_vivo = [a for c in INDESEJADOS_AO_VIVO for a in lista(f"unwanted_sounds/{c}")[:1]]
    return {"campainha": {"dataset": camp_ds, "ao_vivo": camp_vivo},
            "ambiente": {"dataset": amb_ds, "ao_vivo": amb_vivo}}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--esc50", type=Path, required=True)
    ap.add_argument("--visualfy", type=Path, required=True, help="pasta few_shot_vfy_zenodo do zip do Visualfy")
    a = ap.parse_args()
    sel = selecionar(a.esc50 / "meta" / "esc50.csv")
    for p in [BRUTOS / c for c in ("campainha", "batida_porta", "ambiente")] + [AO_VIVO]:
        if p.exists():  # só as pastas que este script gera; o zip baixado em brutos/ fica intacto
            shutil.rmtree(p)
        p.mkdir(parents=True)
    creditos = []
    for classe, conjuntos in sel.items():
        for i, x in enumerate(conjuntos["dataset"], 1):
            destino = BRUTOS / classe / f"{classe}.esc50.{i:02d}.wav"
            destino.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(a.esc50 / "audio" / x["filename"], destino)
            creditos.append((destino.name, x["filename"], f"esc50:{x['category']}", "dataset"))
        for i, x in enumerate(conjuntos["ao_vivo"], 1):
            destino = AO_VIVO / f"{classe}_{i}_{x['category']}.wav"
            destino.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(a.esc50 / "audio" / x["filename"], destino)
            creditos.append((destino.name, x["filename"], f"esc50:{x['category']}", "ao_vivo"))
    # Visualfy: campainhas reais e mais sons indesejados no ambiente
    vfy = selecionar_visualfy(a.visualfy)
    n_amb = len(sel["ambiente"]["dataset"])
    for i, arq in enumerate(vfy["campainha"]["dataset"], 1):
        destino = BRUTOS / "campainha" / f"campainha.visualfy.{i:02d}.wav"
        shutil.copy(arq, destino)
        creditos.append((destino.name, arq.relative_to(a.visualfy).as_posix(), "visualfy", "dataset"))
    for i, arq in enumerate(vfy["campainha"]["ao_vivo"], 1):
        destino = AO_VIVO / f"campainha_{i}_{arq.parent.name}.wav"
        shutil.copy(arq, destino)
        creditos.append((destino.name, arq.relative_to(a.visualfy).as_posix(), "visualfy", "ao_vivo"))
    for i, arq in enumerate(vfy["ambiente"]["dataset"], n_amb + 1):
        destino = BRUTOS / "ambiente" / f"ambiente.visualfy.{i:02d}.wav"
        shutil.copy(arq, destino)
        creditos.append((destino.name, arq.relative_to(a.visualfy).as_posix(), "visualfy", "dataset"))
    n_vivo = len(sel["ambiente"]["ao_vivo"])
    for i, arq in enumerate(vfy["ambiente"]["ao_vivo"], n_vivo + 1):
        destino = AO_VIVO / f"ambiente_{i}_{arq.parent.name}.wav"
        shutil.copy(arq, destino)
        creditos.append((destino.name, arq.relative_to(a.visualfy).as_posix(), "visualfy", "ao_vivo"))
    with open(DADOS / "creditos_sons.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["arquivo_local", "arquivo_original", "base_ou_categoria", "uso"])
        w.writerows(creditos)
    print(f"Dataset bruto em {BRUTOS} (60 clipes) e teste ao vivo em {AO_VIVO} (15 clipes).")
    print("Próximo passo: python preparar_audios.py && python verificar_dataset.py")


if __name__ == "__main__":
    main()
