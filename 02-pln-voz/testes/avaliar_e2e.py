"""Teste ponta a ponta: 10 conversas de 3 turnos, com latência por etapa.

    python testes/avaliar_e2e.py            # usa os modelos do .env
    python testes/avaliar_e2e.py --demo     # módulos falsos (só confere o fluxo)

Lê testes/conversas_e2e.csv e os áudios em audios_teste/e2e/ (o grupo grava seguindo a
coluna `pergunta_planejada`). Grava evidencias/e2e_resultados.csv e e2e_resumo.md.

O progresso é gravado a cada turno e `--retomar` continua de onde parou (conversas já concluídas e sem
erro são puladas). Um erro num turno vira um resultado com motivo "erro" e a rodada segue; os turnos com
erro ficam de fora das médias de latência. Escolha a configuração pelas variáveis STT_MODEL, LLM_PROVIDER,
LLM_MODEL, TTS_ENGINE e LLM_TIMEOUT_S, e use --saida para guardar cada configuração em uma pasta.
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


def executar(stt, llm, base, tts, linhas: list[dict], pasta: Path, ao_terminar=None) -> list[dict]:
    conversas: dict[str, list[dict]] = {}
    for l in linhas:
        conversas.setdefault(l["conversa"], []).append(l)
    resultados = []
    for turnos in conversas.values():
        pipeline = PipelineVoz(stt, Assistente(llm, base), tts)  # memória nova por conversa
        for l in sorted(turnos, key=lambda x: int(x["turno"])):
            try:
                r = pipeline.turno(str(pasta / l["arquivo"]))
                resultados.append({"conversa": l["conversa"], "turno": l["turno"], "transcricao": r.transcricao,
                                   "resposta": r.resposta_texto, "motivo": r.motivo,
                                   **{e: round(r.latencias[e], 3) for e in ETAPAS}})
            except Exception as erro:  # noqa: BLE001 - uma falha não pode perder a rodada inteira
                print(f"  {l['conversa']} turno {l['turno']}: erro ({type(erro).__name__}); segue", file=sys.stderr)
                resultados.append({"conversa": l["conversa"], "turno": l["turno"], "transcricao": "",
                                   "resposta": f"[ERRO: {type(erro).__name__}]", "motivo": "erro",
                                   **{e: 0.0 for e in ETAPAS}})
            if ao_terminar:
                ao_terminar(resultados[-1])
    return resultados


def conversas_completas(resultados: list[dict], linhas: list[dict]) -> set[str]:
    """Conversas com todos os turnos nos resultados e sem erro (as demais são refeitas, pois a memória é por conversa)."""
    esperados: dict[str, int] = {}
    for l in linhas:
        esperados[l["conversa"]] = esperados.get(l["conversa"], 0) + 1
    feitos: dict[str, int] = {}
    for r in resultados:
        if r["motivo"] != "erro":
            feitos[r["conversa"]] = feitos.get(r["conversa"], 0) + 1
    return {c for c, n in esperados.items() if feitos.get(c, 0) >= n}


def resumir(resultados: list[dict], configuracao: str = "") -> str:
    conversas = {r["conversa"] for r in resultados}
    validos = [r for r in resultados if r["motivo"] != "erro"] or resultados
    linhas = [[e, fmt(media([float(r[e]) for r in validos]), 2), fmt(max(float(r[e]) for r in validos), 2)]
              for e in ETAPAS]
    motivos = {}
    for r in resultados:
        motivos[r["motivo"]] = motivos.get(r["motivo"], 0) + 1
    erros = sum(1 for r in resultados if r["motivo"] == "erro")
    return "\n".join([
        "# Ponta a ponta: resultados\n",
        (f"Configuração: {configuracao}.\n" if configuracao else "")
        + f"{len(conversas)} conversas, {len(resultados)} turnos"
        + (f" ({erros} com erro, fora das médias)" if erros else "") + ".\n",
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
    ap.add_argument("--retomar", action="store_true", help="continua uma rodada interrompida")
    a = ap.parse_args()

    linhas = ler_csv(a.manifesto)
    faltando = [l["arquivo"] for l in linhas if not (a.pasta / l["arquivo"]).is_file()]
    if faltando:
        print(f"Faltam {len(faltando)} áudios em {a.pasta}:\n  " + "\n  ".join(faltando))
        return 1

    from componentes import carregar_componentes
    stt, llm, base, tts = carregar_componentes(a.demo, apagar_audio=False)  # áudios de teste não são apagados
    a.saida.mkdir(parents=True, exist_ok=True)
    destino = a.saida / "e2e_resultados.csv"
    configuracao = f"STT {stt.nome}, LLM {llm.nome}, TTS {tts.nome}"
    anteriores = ler_csv(destino) if a.retomar and destino.exists() else []
    feitas = conversas_completas(anteriores, linhas)
    anteriores = [r for r in anteriores if r["conversa"] in feitas]
    pendentes = [l for l in linhas if l["conversa"] not in feitas]
    if feitas:
        print(f"retomando: {len(feitas)} conversas já concluídas, {len(pendentes)} turnos a fazer")
    novos: list[dict] = []

    def gravar(r=None):
        if r is not None:
            novos.append(r)
        tmp = destino.with_suffix(".tmp")
        escrever_csv(tmp, anteriores + novos)
        tmp.replace(destino)
        (a.saida / "e2e_resumo.md").write_text(resumir(anteriores + novos, configuracao), encoding="utf-8")

    executar(stt, llm, base, tts, pendentes, a.pasta, ao_terminar=gravar)
    gravar()
    print((a.saida / "e2e_resumo.md").read_text(encoding="utf-8"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
