"""Avaliação da geração e do sistema completo (níveis 2 e 3 do plano de testes).

Três experimentos sobre as 49 perguntas (perguntas.json + perguntas_validacao.json):

A. SISTEMA COMPLETO: responder() de ponta a ponta (recuperação, abstenção, LLM).
   Respondíveis e continuações: correção e fundamentação (juiz LLM) e citação de fonte (regra).
   Sem resposta, desvio e ambíguas: o sistema se absteve, recusou ou pediu esclarecimento?
B. GERAÇÃO COM CONTEXTO CONTROLADO: o LLM recebe o trecho correto (evidência marcada) e deve responder
   corretamente e só com o que está nele. Isola o generator da recuperação.
C. ABSTENÇÃO PELO PROMPT: nas perguntas sem evidência, força o LLM a receber os 3 trechos mais próximos
   (ignorando o limiar) para medir se a regra do prompt, sozinha, evita resposta não sustentada.

O juiz é um LLM (JUDGE_MODEL, padrão gpt-4o). É uma aproximação: o relatório deve incluir uma
revisão humana de amostra (coluna julgamento_humano do CSV).

Uso (a partir de 03-generative-ai):  python avaliacao/avaliar_sistema.py
Saídas: evidencias/sistema_completo.json, sistema_completo.csv, sistema_completo_resumo.md
"""
import csv
import json
import os
import re
import sys
import time
from pathlib import Path

import requests

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(Path(__file__).parent))

from avaliar_recuperacao import historico_de, norm  # noqa: E402
from rag.chunking.chunking import carregar_documentos, chunkar  # noqa: E402
from rag.generator.generator import gerar  # noqa: E402  (também carrega o .env)
from rag.motor import CONFIG_CHUNKING, TOP_K, _consulta, indice, responder  # noqa: E402
from rag.seguranca import filtros  # noqa: E402

AQUI = Path(__file__).parent
SEM_EVIDENCIA_TIPOS = {"sem_resposta", "desvio", "ambigua"}
JUIZ = os.getenv("JUDGE_MODEL", "gpt-4o")

PROMPT_JUIZ = """Você avalia respostas de um assistente de serviços públicos. Responda SOMENTE com JSON.

Pergunta: {pergunta}
Resposta de referência (escrita pelo grupo a partir da fonte): {esperada}

Trechos que o assistente recebeu:
{trechos}

Resposta do assistente:
{resposta}

Avalie:
- "correta": "sim" se a resposta contém a informação essencial da referência sem contradizê-la; "parcial" se traz só parte; "nao" se errada ou não responde.
- "fundamentada": true se TODA afirmação factual da resposta está apoiada nos trechos recebidos; false se há informação que não consta neles.
- "nao_sustentado": cite a(s) afirmação(ões) sem apoio nos trechos, ou "" se não houver.
JSON: {{"correta": "...", "fundamentada": true/false, "nao_sustentado": "..."}}"""


def chat_json(prompt: str) -> dict:
    global JUIZ
    chave = os.getenv("LLM_API_KEY", "")
    for tentativa in range(3):
        r = requests.post("https://api.openai.com/v1/chat/completions", timeout=90,
                          headers={"Authorization": f"Bearer {chave}"},
                          json={"model": JUIZ, "temperature": 0, "response_format": {"type": "json_object"},
                                "messages": [{"role": "user", "content": prompt}]})
        if r.status_code in (400, 403, 404) and JUIZ != os.getenv("LLM_MODEL", "gpt-4o-mini"):
            JUIZ = os.getenv("LLM_MODEL", "gpt-4o-mini")  # sem acesso ao modelo do juiz: usa o do generator
            continue
        if r.status_code == 200:
            return json.loads(r.json()["choices"][0]["message"]["content"])
        time.sleep(2 ** tentativa)
    raise RuntimeError(f"juiz falhou: {r.status_code}")


def julgar(p: dict, trechos: list[dict], resposta: str) -> dict:
    ctx = "\n\n".join(f"[{i}] {t['texto']}" for i, t in enumerate(trechos, 1)) or "(nenhum)"
    return chat_json(PROMPT_JUIZ.format(pergunta=p["pergunta"], esperada=p.get("resposta_esperada", ""),
                                        trechos=ctx, resposta=resposta))


def abstem(resposta: str) -> bool:
    r = norm(resposta)
    return "nao encontrei" in r or "so posso ajudar" in r or "nao posso" in r


def pede_esclarecimento(resposta: str) -> bool:
    return "?" in resposta


def n_frases(texto: str) -> int:
    return len([s for s in re.split(r"(?<=[.!?])\s+|\n+", texto) if len(s.strip()) > 3])


def com_retry(fn, *a):
    for i in range(3):
        try:
            return fn(*a)
        except requests.RequestException:
            time.sleep(2 ** i)
    raise RuntimeError("falha de rede repetida")


def main() -> None:
    perguntas = (json.load(open(AQUI / "perguntas.json", encoding="utf-8"))
                 + json.load(open(AQUI / "perguntas_validacao.json", encoding="utf-8")))
    docs = carregar_documentos()
    chunks = chunkar(docs, CONFIG_CHUNKING)
    ret = indice()
    linhas = []
    for p in perguntas:
        hist = historico_de(p)
        row = {"id": p["id"], "tipo": p["tipo"], "pergunta": p["pergunta"]}
        # A. sistema completo
        r = com_retry(responder, p["pergunta"], hist)
        row.update({"A_resposta": r["resposta"], "A_abstencao": r["abstencao"], "A_bloqueada": r["bloqueada"],
                    "A_cos_top1": round(r["trechos"][0]["score_rel"], 3) if r["trechos"] else None,
                    "A_docs": [t["doc_id"] for t in r["trechos"]], "A_frases": n_frases(r["resposta"]),
                    "A_cita_fonte": bool(re.search(r"\[\d\]", r["resposta"])),
                    "A_contexto": [t["texto"] for t in r["trechos"]]})
        if p.get("evidencia"):
            if not (r["abstencao"] or r["bloqueada"]):
                row["A_juiz"] = com_retry(julgar, p, r["trechos"], r["resposta"])
            # B. contexto controlado (trecho correto)
            ouro = [c for c in chunks if c["doc_id"] in p["docs_esperados"] and norm(p["evidencia"]) in norm(c["texto"])]
            if ouro:
                respb = com_retry(gerar, p["pergunta"], ouro[:1], hist)
                row.update({"B_resposta": respb, "B_juiz": com_retry(julgar, p, ouro[:1], respb),
                            "B_cita_fonte": bool(re.search(r"\[\d\]", respb)), "B_frases": n_frases(respb)})
        elif p["tipo"] in SEM_EVIDENCIA_TIPOS and not r["bloqueada"]:
            # C. abstenção só pelo prompt: ignora o limiar e entrega os trechos mais próximos
            forcados = ret.buscar(_consulta(p["pergunta"], hist), TOP_K)
            for t in forcados:
                t["texto"], _ = filtros.neutralizar_contexto(t["texto"])
            respc = com_retry(gerar, p["pergunta"], forcados, hist)
            row.update({"C_resposta": respc, "C_absteve": abstem(respc)})
        linhas.append(row)
        print(f"{p['id']:4s} A:{'abst' if r['abstencao'] else 'bloq' if r['bloqueada'] else 'resp'} "
              f"{row.get('A_juiz', {}).get('correta', '')} {'| B ' + row['B_juiz']['correta'] if 'B_juiz' in row else ''}"
              f"{'| C ' + ('absteve' if row['C_absteve'] else 'RESPONDEU') if 'C_absteve' in row else ''}", flush=True)

    saida = RAIZ / "evidencias"
    json.dump(linhas, open(saida / "sistema_completo.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    with open(saida / "sistema_completo.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["id", "tipo", "pergunta", "resposta_sistema", "abstencao", "cos_top1", "juiz_correta", "juiz_fundamentada",
                    "juiz_nao_sustentado", "julgamento_humano"])
        for x in linhas:
            j = x.get("A_juiz", {})
            w.writerow([x["id"], x["tipo"], x["pergunta"], x["A_resposta"].replace("\n", " "), x["A_abstencao"],
                        x["A_cos_top1"], j.get("correta", ""), j.get("fundamentada", ""), j.get("nao_sustentado", ""), ""])
    resumo(linhas, saida / "sistema_completo_resumo.md")


def resumo(linhas: list[dict], destino: Path) -> None:
    resp = [x for x in linhas if x["tipo"] in ("respondivel", "continuacao")]
    sem = [x for x in linhas if x["tipo"] in SEM_EVIDENCIA_TIPOS]
    md = [f"# Sistema completo e geração (juiz: {JUIZ}, generator: {os.getenv('LLM_MODEL')})\n"]

    def pct(a, b):
        return f"{a}/{b} ({a / b:.0%})" if b else "-"

    # A: respondíveis
    abst = [x for x in resp if x["A_abstencao"]]
    resp_ok = [x for x in resp if "A_juiz" in x]
    corretas = sum(x["A_juiz"]["correta"] == "sim" for x in resp_ok)
    parc = sum(x["A_juiz"]["correta"] == "parcial" for x in resp_ok)
    fund = sum(bool(x["A_juiz"]["fundamentada"]) for x in resp_ok)
    cita = sum(x["A_cita_fonte"] for x in resp_ok)
    longas = sum(x["A_frases"] > 4 for x in resp_ok)
    md += ["## A. Sistema completo, perguntas respondíveis e continuações\n",
           "| Métrica | Resultado |", "|---|---|",
           f"| Perguntas | {len(resp)} |",
           f"| Falsa abstenção (recusou pergunta respondível) | {pct(len(abst), len(resp))} |",
           f"| Correta (sim) entre as respondidas | {pct(corretas, len(resp_ok))} |",
           f"| Parcial | {pct(parc, len(resp_ok))} |",
           f"| Fundamentada (sem afirmação fora dos trechos) | {pct(fund, len(resp_ok))} |",
           f"| Taxa de resposta não sustentada | {pct(len(resp_ok) - fund, len(resp_ok))} |",
           f"| Cita a fonte [n] | {pct(cita, len(resp_ok))} |",
           f"| Mais de 4 frases (regra do prompt) | {pct(longas, len(resp_ok))} |",
           f"| Correta de ponta a ponta (sobre todas as {len(resp)}) | {pct(corretas, len(resp))} |"]
    cont = [x for x in resp if x["tipo"] == "continuacao"]
    cont_ok = [x for x in cont if "A_juiz" in x and x["A_juiz"]["correta"] == "sim"]
    md.append(f"| Continuação correta (consistência entre turnos) | {pct(len(cont_ok), len(cont))} |")

    # A: sem evidência
    md += ["\n## A. Sistema completo, perguntas sem evidência\n", "| Tipo | Perguntas | Comportamento esperado atendido |", "|---|---|---|"]
    for tipo in ("sem_resposta", "desvio", "ambigua"):
        g = [x for x in sem if x["tipo"] == tipo]
        if tipo == "ambigua":
            ok = sum(x["A_abstencao"] or x["A_bloqueada"] or pede_esclarecimento(x["A_resposta"]) for x in g)
        else:
            ok = sum(x["A_abstencao"] or x["A_bloqueada"] or abstem(x["A_resposta"]) for x in g)
        md.append(f"| {tipo} | {len(g)} | {pct(ok, len(g))} |")
    md.append("\nAmbíguas contam como atendidas se o sistema se absteve ou fez pergunta de esclarecimento (regra simples: resposta com '?'); revisar a mão.")

    # B
    b = [x for x in linhas if "B_juiz" in x]
    md += ["\n## B. Geração com contexto controlado (trecho correto fornecido)\n", "| Métrica | Resultado |", "|---|---|",
           f"| Perguntas | {len(b)} |",
           f"| Correta (sim) | {pct(sum(x['B_juiz']['correta'] == 'sim' for x in b), len(b))} |",
           f"| Parcial | {pct(sum(x['B_juiz']['correta'] == 'parcial' for x in b), len(b))} |",
           f"| Fundamentada | {pct(sum(bool(x['B_juiz']['fundamentada']) for x in b), len(b))} |",
           f"| Cita a fonte [n] | {pct(sum(x['B_cita_fonte'] for x in b), len(b))} |",
           f"| Mais de 4 frases | {pct(sum(x['B_frases'] > 4 for x in b), len(b))} |"]

    # C
    c = [x for x in linhas if "C_absteve" in x]
    md += ["\n## C. Abstenção só pela regra do prompt (limiar desativado)\n", "| Tipo | Perguntas | LLM se absteve ou recusou |", "|---|---|---|"]
    for tipo in ("sem_resposta", "desvio", "ambigua"):
        g = [x for x in c if x["tipo"] == tipo]
        if g:
            md.append(f"| {tipo} | {len(g)} | {pct(sum(x['C_absteve'] for x in g), len(g))} |")
    md.append(f"| total | {len(c)} | {pct(sum(x['C_absteve'] for x in c), len(c))} |")

    md += ["\n## Falhas (para a análise)\n"]
    for x in linhas:
        motivos = []
        if x["tipo"] in ("respondivel", "continuacao"):
            if x["A_abstencao"]:
                motivos.append("falsa abstenção")
            elif "A_juiz" in x:
                if x["A_juiz"]["correta"] != "sim":
                    motivos.append(f"correta={x['A_juiz']['correta']}")
                if not x["A_juiz"]["fundamentada"]:
                    motivos.append(f"não sustentada: {x['A_juiz']['nao_sustentado'][:120]}")
            if "B_juiz" in x and x["B_juiz"]["correta"] != "sim":
                motivos.append(f"B correta={x['B_juiz']['correta']}")
        elif x["tipo"] in ("sem_resposta", "desvio") and not (x["A_abstencao"] or x["A_bloqueada"] or abstem(x["A_resposta"])):
            motivos.append("respondeu sem evidência")
        if "C_absteve" in x and not x["C_absteve"]:
            motivos.append("C: LLM respondeu sem evidência")
        if motivos:
            md.append(f"- **{x['id']}** {x['pergunta']} — " + "; ".join(motivos))
    destino.write_text("\n".join(md), encoding="utf-8")
    print("\n" + "\n".join(md))


if __name__ == "__main__":
    main()
