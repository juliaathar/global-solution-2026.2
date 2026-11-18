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
    r"voc[eê] deve (agora )?(responder|obedecer)|system prompt|reveal your|ignore previous)", re.I)


def pedido_malicioso(pergunta: str) -> bool:
    return bool(_VAZAMENTO.search(pergunta))


def evidencia_fraca(trechos: list[dict]) -> bool:
    return not trechos or trechos[0]["score_rel"] < LIMIAR_ABSTENCAO


def neutralizar_contexto(texto: str) -> tuple[str, bool]:
    """Remove linhas que parecem comandos ao modelo. Devolve (texto, houve_remocao)."""
    linhas = texto.split("\n")
    limpo = [l for l in linhas if not _INJECAO_NO_DOC.search(l)]
    return "\n".join(limpo), len(limpo) != len(linhas)
