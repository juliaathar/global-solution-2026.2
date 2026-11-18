"""Teste ponta a ponta: 10 conversas de 3 turnos, com latência por etapa.

    python testes/avaliar_e2e.py            # usa os modelos do .env
    python testes/avaliar_e2e.py --demo     # módulos falsos (só confere o fluxo)

Lê testes/conversas_e2e.csv e os áudios em audios_teste/e2e/ (o grupo grava seguindo a
coluna `pergunta_planejada`). Grava evidencias/e2e_resultados.csv e e2e_resumo.md.
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from util import (AUDIOS, EVIDENCIAS, TESTES, escrever_csv, fmt, ler_csv,  # noqa: E402
                  media, tabela_md)

from llm import Assistente  # noqa: E402
from pipeline import PipelineVoz  # noqa: E402

ETAPAS = ["stt", "llm_rag", "adaptacao", "tts", "total"]


def executar(stt, llm, base, tts, linhas: list[dict], pasta: Path) -> list[dict]:
    conversas: dict[str, list[dict]] = {}
    for l in linhas:
        conversas.setdefault(l["conversa"], []).append(l)
    resultados = []
    for turnos in conversas.values():
        pipeline = PipelineVoz(stt, Assistente(llm, base), tts)  # memória nova por conversa
        for l in sorted(turnos, key=lambda x: int(x["turno"])):
            r = pipeline.turno(str(pasta / l["arquivo"]))
            resultados.append({"conversa": l["conversa"], "turno": l["turno"], "transcricao": r.transcricao,
                               "resposta": r.resposta_texto, "motivo": r.motivo,
                               **{e: round(r.latencias[e], 3) for e in ETAPAS}})
    return resultados


def resumir(resultados: list[dict]) -> str:
    conversas = {r["conversa"] for r in resultados}
    linhas = [[e, fmt(media([r[e] for r in resultados]), 2), fmt(max(r[e] for r in resultados), 2)]
              for e in ETAPAS]
    motivos = {}
    for r in resultados:
        motivos[r["motivo"]] = motivos.get(r["motivo"], 0) + 1
    return "\n".join([
        "# Ponta a ponta: resultados\n",
        f"{len(conversas)} conversas, {len(resultados)} turnos.\n",
        tabela_md(["Etapa", "Média (s)", "Máximo (s)"], linhas),
        "\n`total` é o tempo da pergunta até a resposta estar pronta para tocar, isto é, o início da fala.\n",
        "## Como as respostas foram geradas\n",
        tabela_md(["Origem", "Turnos"], sorted(motivos.items())),
    ])


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--demo", action="store_true")
    ap.add_argument("--manifesto", type=Path, default=TESTES / "conversas_e2e.csv")
    ap.add_argument("--pasta", type=Path, default=AUDIOS / "e2e")
    ap.add_argument("--saida", type=Path, default=EVIDENCIAS, help="pasta dos resultados")
    a = ap.parse_args()

    linhas = ler_csv(a.manifesto)
    faltando = [l["arquivo"] for l in linhas if not (a.pasta / l["arquivo"]).is_file()]
    if faltando:
        print(f"Faltam {len(faltando)} áudios em {a.pasta}:\n  " + "\n  ".join(faltando))
        return 1

    from componentes import carregar_componentes
    stt, llm, base, tts = carregar_componentes(a.demo, apagar_audio=False)  # áudios de teste não são apagados
    resultados = executar(stt, llm, base, tts, linhas, a.pasta)
    a.saida.mkdir(parents=True, exist_ok=True)
    escrever_csv(a.saida / "e2e_resultados.csv", resultados)
    (a.saida / "e2e_resumo.md").write_text(resumir(resultados), encoding="utf-8")
    print((a.saida / "e2e_resumo.md").read_text(encoding="utf-8"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
