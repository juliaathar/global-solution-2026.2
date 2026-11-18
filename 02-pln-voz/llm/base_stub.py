"""Base de conhecimento provisória (busca por palavras-chave).

Mesma interface do RAG de 03-generative-ai. Quando o RAG existir, basta
criar um adaptador com `buscar(pergunta, k) -> list[Trecho]` e trocar aqui.
Os textos abaixo são EXEMPLOS fictícios para desenvolvimento, não fontes oficiais.
"""
from interfaces import Trecho

from .texto import palavras

CORPUS_EXEMPLO = [
    Trecho("A UBS atende de segunda a sexta, das sete às dezessete horas. Leve documento com foto e cartão do SUS.", "exemplo-ubs"),
    Trecho("O CRAS orienta sobre benefícios sociais e o Cadastro Único. Leve documento com foto e comprovante de residência.", "exemplo-cras"),
    Trecho("A segunda via do RG é feita no posto de identificação. Leve certidão de nascimento ou casamento e comprovante de residência.", "exemplo-rg"),
    Trecho("Buraco na rua, poste apagado e lixo acumulado podem ser relatados pelo EloBairro, que gera um protocolo.", "exemplo-elobairro"),
]


class BaseStub:
    def __init__(self, corpus: list[Trecho] | None = None):
        self.corpus = corpus or CORPUS_EXEMPLO

    def buscar(self, pergunta: str, k: int = 3) -> list[Trecho]:
        q = palavras(pergunta)
        pontuados = [(len(q & palavras(t.texto)), t) for t in self.corpus]
        return [t for p, t in sorted(pontuados, key=lambda x: -x[0])[:k] if p > 0]
