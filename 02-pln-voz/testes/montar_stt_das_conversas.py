"""Monta o conjunto de teste do STT (20 áudios) reaproveitando gravações das conversas.

    python testes/montar_stt_das_conversas.py                         # grava em audios_teste/stt e no manifesto
    python testes/montar_stt_das_conversas.py --saida-audios DIR --saida-manifesto ARQ.csv   # só para avaliar

Por que existe: o enunciado pede 20 áudios gravados pelo grupo, com pelo menos 3 vozes e 5 com ruído. As
conversas (c01 a c10) já têm as 3 vozes, então 15 áudios limpos vêm delas e só os 5 com ruído são gravados à parte
(stt_03, stt_07, stt_11, stt_15 e stt_19).

Regra de escolha dos 15 limpos (fixa, definida ANTES de olhar o WER, para não enviesar o resultado): os 5 primeiros
áudios de cada voz, na ordem das conversas. Os originais vêm de audios_teste/entrada/ (mesmo mapeamento.csv do
organizar_audios.py). Os 5 com ruído são todos da voz A: a comparação de ruído fica na mesma pessoa.
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import organizar_audios as oa  # noqa: E402
from util import AUDIOS, escrever_csv, ler_csv  # noqa: E402

# vaga do manifesto -> (voz, código da conversa). Voz A = Edgar, B = Bruno, C = Júlia.
LIMPOS = {
    "stt_01": ("A", "c01_t1"), "stt_02": ("A", "c01_t2"), "stt_04": ("A", "c01_t3"),
    "stt_05": ("A", "c02_t1"), "stt_06": ("A", "c02_t2"),
    "stt_08": ("B", "c04_t1"), "stt_09": ("B", "c04_t2"), "stt_10": ("B", "c04_t3"),
    "stt_12": ("B", "c05_t1"), "stt_13": ("B", "c05_t2"),
    "stt_14": ("C", "c07_t1"), "stt_16": ("C", "c07_t2"), "stt_17": ("C", "c07_t3"),
    "stt_18": ("C", "c08_t1"), "stt_20": ("C", "c08_t2"),
}
RUIDOSOS = ("stt_03", "stt_07", "stt_11", "stt_15", "stt_19")  # gravados à parte, voz A
CAMPOS = ["arquivo", "falante", "ruido", "faixa_etaria", "sotaque", "referencia"]


def montar(entrada: Path, saida_audios: Path, saida_manifesto: Path, modelo_manifesto: Path | None = None,
           planejadas: Path | None = None) -> tuple[list[dict], list[str]]:
    """Devolve (linhas do manifesto, problemas). Só grava se não houver problema."""
    esperados = oa.codigos_esperados()
    achados, problemas = oa.identificar(entrada, esperados)
    vozes = oa.ler_vozes(entrada)
    plano = {Path(l["arquivo"]).stem: l["pergunta_planejada"]
             for l in ler_csv(planejadas or oa.TESTES / "conversas_e2e.csv")}
    base = {Path(l["arquivo"]).stem: l for l in ler_csv(modelo_manifesto or AUDIOS / "manifesto_stt.csv")}

    linhas, origens = [], {}
    for vaga in sorted(base):
        if vaga in LIMPOS:
            voz, cod = LIMPOS[vaga]
            ref, ruido, origem = plano[cod], "nao", achados.get(cod)
            quem = cod
        elif vaga in RUIDOSOS:
            voz, ref, ruido, origem, quem = "A", base[vaga]["referencia"], "sim", achados.get(vaga), vaga
        else:
            problemas.append(f"vaga {vaga} sem regra em LIMPOS nem em RUIDOSOS")
            continue
        if origem is None:
            problemas.append(f"falta o áudio de {quem} (vaga {vaga})")
            continue
        v = vozes.get(voz, {})
        linhas.append({"arquivo": f"{vaga}.wav", "falante": voz, "ruido": ruido,
                       "faixa_etaria": v.get("faixa_etaria", ""), "sotaque": v.get("sotaque", ""), "referencia": ref})
        origens[vaga] = origem
    if problemas:
        return linhas, problemas
    for vaga, origem in origens.items():
        oa.gravar_wav(saida_audios / f"{vaga}.wav", oa.carregar(origem))
    escrever_csv(saida_manifesto, linhas, CAMPOS)
    return linhas, []


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--entrada", type=Path, default=AUDIOS / "entrada")
    ap.add_argument("--saida-audios", type=Path, default=AUDIOS / "stt")
    ap.add_argument("--saida-manifesto", type=Path, default=AUDIOS / "manifesto_stt.csv")
    a = ap.parse_args()
    linhas, problemas = montar(a.entrada, a.saida_audios, a.saida_manifesto)
    if problemas:
        print("Não montei o conjunto:\n  " + "\n  ".join(problemas))
        return 1
    vozes = {}
    for l in linhas:
        vozes[l["falante"]] = vozes.get(l["falante"], 0) + 1
    print(f"{len(linhas)} áudios em {a.saida_audios}; por voz: {vozes}; com ruído: {sum(l['ruido'] == 'sim' for l in linhas)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
