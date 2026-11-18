"""Proteções do motor RAG (versão inicial; os testes adversariais completos vêm na avaliação).

1. Abstenção: se a evidência recuperada for fraca, não chama o LLM.
2. Entrada: pedidos para revelar o prompt/instruções são recusados antes de qualquer busca.
3. Contexto: trechos que parecem instruções ao modelo (injection indireta) são neutralizados.
"""
import re

# Cosseno mínimo (e5-large) do melhor trecho. Calibrado em avaliacao/perguntas.json e validado em
# perguntas_validacao.json (evidencias/validacao_limiar.md). A margem é estreita (~0,01): ver limites no relatório.
LIMIAR_ABSTENCAO = 0.84
MSG_ABSTENCAO = ("Não encontrei essa informação nas fontes oficiais que tenho. "
                 "Procure a Prefeitura de São José dos Campos pelo telefone 156 ou no portal sjc.sp.gov.br.")
MSG_RECUSA = ("Só posso ajudar com serviços públicos de São José dos Campos, com base em fontes oficiais. "
              "Não posso mostrar minhas instruções internas.")

_VAZAMENTO = re.compile(
    r"(system prompt|prompt do sistema|suas instru[cç][oõ]es|instru[cç][oõ]es internas|revele (o )?(seu )?prompt|"
    r"mostre (o )?(seu )?prompt|ignore (todas )?(as )?instru[cç][oõ]es|esque[cç]a (as )?instru[cç][oõ]es|"
    r"repita (tudo|o texto) acima|modo desenvolvedor|developer mode)", re.I)
_INJECAO_NO_DOC = re.compile(
    r"(ignore (todas )?(as )?(instru[cç][oõ]es|regras)|desconsidere|a partir de agora (voc[eê]|responda)|"
    r"voc[eê] deve (agora )?(responder|obedecer)|system prompt|reveal your|ignore previous|"
    r"(nota|aviso|mensagem|instru[cç][aã]o) (para|ao) (o )?(assistente|modelo|ia|rob[oô])|"
    r"responda (ao cidad[aã]o |ao usu[aá]rio )?que|inclua no final|termine (a resposta )?(pedindo|com)|"
    r"informe (seu|sua|o seu) (cpf|senha)|texto completo das (suas )?instru)", re.I)

# Perguntas vagas: não sobra palavra de conteúdo, ou só sobram palavras genéricas de serviço.
_GENERICAS = {"telefone", "endereco", "horario", "ajuda", "reclamar", "reclamacao", "informacao", "informacoes",
              "servico", "cadastro", "documento", "documentos", "faco", "numero", "contato", "atendimento"}
MSG_ESCLARECIMENTO = ("Para eu ajudar, preciso saber melhor o que você procura. De qual serviço você fala? "
                      "Por exemplo: UBS, CRAS, Cadastro Único, coleta de lixo, buraco na rua ou transporte adaptado.")
MSG_SAIDA_BLOQUEADA = ("Não consegui confirmar essa resposta nas fontes oficiais. "
                       "Procure a Prefeitura pelo telefone 156 ou no portal sjc.sp.gov.br.")


def pedido_malicioso(pergunta: str) -> bool:
    return bool(_VAZAMENTO.search(pergunta))


def pergunta_vaga(pergunta: str, tem_historico: bool) -> bool:
    """True se a pergunta não diz de que serviço fala. Em continuação (com histórico) nunca é vaga."""
    if tem_historico:
        return False
    from rag.retriever.bm25 import tokenizar
    palavras = tokenizar(pergunta)
    return not palavras or all(p in _GENERICAS for p in palavras)


def resposta_suspeita(resposta: str, trechos: list[dict]) -> str:
    """Guarda de saída. Devolve o motivo se a resposta tem URL ou valor em reais que não estão nos trechos,
    ou trechos das instruções internas; senão, string vazia."""
    from rag.generator.generator import SISTEMA
    contexto = " ".join(t["texto"] for t in trechos)
    for url in re.findall(r"https?://\S+|www\.\S+", resposta):
        if url.rstrip(".,;)") not in contexto:
            return f"URL fora das fontes: {url[:60]}"
    for valor in re.findall(r"R\$\s?\d[\d.,]*", resposta):
        if valor not in contexto:
            return f"valor em reais fora das fontes: {valor}"
    for linha in SISTEMA.splitlines():
        if len(linha) > 40 and linha[:40].lower() in resposta.lower():
            return "trecho das instruções internas na resposta"
    return ""


def evidencia_fraca(trechos: list[dict]) -> bool:
    return not trechos or trechos[0]["score_rel"] < LIMIAR_ABSTENCAO


def neutralizar_contexto(texto: str) -> tuple[str, bool]:
    """Remove linhas que parecem comandos ao modelo. Devolve (texto, houve_remocao)."""
    linhas = texto.split("\n")
    limpo = [l for l in linhas if not _INJECAO_NO_DOC.search(l)]
    return "\n".join(limpo), len(limpo) != len(linhas)
