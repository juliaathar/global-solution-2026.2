"""Assistente: system prompt, memória da conversa, guardas e chamada ao LLM com RAG."""
import re
import unicodedata

from interfaces import LLM, BaseConhecimento, Mensagem, Trecho

from .texto import compartilham_radical, palavras

SYSTEM_PROMPT = """Você é o EloBairro, um assistente de voz que orienta moradores sobre serviços públicos do bairro (UBS, CRAS, documentos, benefícios, problemas na rua).

Tom: simples, calmo e acolhedor, como quem fala com uma pessoa idosa. Frases curtas. Sem termos técnicos.

Regras:
- Responda SOMENTE com base nas informações do contexto fornecido. Se a resposta não estiver lá, diga: "Não sei essa informação" e sugira procurar o órgão responsável. Nunca invente endereços, horários ou valores.
- Se o assunto for fora do tema (serviços públicos do bairro), recuse com educação e diga no que você pode ajudar.
- Saúde, assuntos jurídicos e emergências: não dê diagnóstico nem parecer. Oriente a procurar a UBS, a Defensoria Pública ou, em emergência, ligar 192 (SAMU), 193 (Bombeiros) ou 190 (Polícia).
- Use o histórico para entender perguntas de continuação, como "e onde eu faço isso?".
- Responda em no máximo quatro frases, sem listas, sem markdown e sem emojis."""

# Respostas fixas: não passam pelo LLM, então não podem ser inventadas.
MSG_SEM_CONTEXTO = (
    "Não tenho essa informação com segurança. Posso ajudar com serviços públicos do bairro, "
    "como UBS, CRAS e documentos. Para saúde, assuntos jurídicos ou emergência, procure o órgão "
    "competente. Em emergência, ligue 192, 193 ou 190."
)
MSG_EMERGENCIA = (
    "Isso parece uma emergência. Ligue agora para o 192, que é o SAMU, para o 193, dos Bombeiros, "
    "ou para o 190, da Polícia. Não espere."
)

# Fragmentos (sem acento, minúsculos) que indicam risco imediato.
_EMERGENCIA = ("socorro", "emergencia", "infarto", "desmai", "sangrando", "hemorragia", "afogando",
               "incendio", "pegando fogo", "dor no peito", "nao consigo respirar", "overdose",
               "quero me matar", "suicid", "estou sendo agredid", "estao me agredindo",
               "passando mal", "sendo agredid", "sendo assaltad", "agredindo", "assaltando",
               "convuls", "engasg", "sequestr", "mal subito", "acidente grave")

MAX_TURNOS_MEMORIA = 6  # últimos N turnos (pergunta + resposta) enviados ao LLM


def _sem_acento(s: str) -> str:
    s = unicodedata.normalize("NFD", s.lower())
    return re.sub(r"\s+", " ", "".join(c for c in s if unicodedata.category(c) != "Mn"))


# Uma fala só reaproveita a pergunta anterior na busca se parecer continuação: começa com
# "e", "mas" ou "então", ou retoma algo com "isso", "ela", "lá" etc. Sem isso, uma pergunta
# solta (por exemplo, um pedido de piada) herdaria o contexto do assunto anterior e a guarda
# de "não sei" nunca dispararia.
_CONTINUACAO = re.compile(r"^\W*(e|mas|então)\b|"
                          r"\b(isso|isto|disso|nisso|ela|ele|dela|dele|lá|aí|esse|essa|desse|dessa|nesse|nessa)\b")


def parece_continuacao(pergunta: str) -> bool:
    return bool(_CONTINUACAO.search(pergunta.lower()))


def eh_emergencia(pergunta: str) -> bool:
    p = _sem_acento(pergunta)
    return any(f in p for f in _EMERGENCIA)


class Assistente:
    """`ultimo_motivo` diz como a última resposta foi gerada:
    "llm", "sem_contexto" (guarda de 'não sei') ou "emergencia"."""

    def __init__(self, llm: LLM, base: BaseConhecimento, k: int = 3, exigir_contexto: bool = True):
        self.llm = llm
        self.base = base
        self.k = k
        self.exigir_contexto = exigir_contexto
        self.historico: list[Mensagem] = []
        self.ultimo_motivo = ""
        self._ultimo_contexto: list[Trecho] = []

    def _eh_continuacao(self, pergunta: str) -> bool:
        """Só reaproveita a pergunta anterior se a fala (1) tem cara de continuação e (2) não muda
        de assunto: alguma palavra dela precisa ter raiz em comum com a conversa anterior. Se não tiver,
        cai na busca sozinha e, sem contexto, na guarda de 'não sei' (a falha segura)."""
        if len(self.historico) < 2 or not parece_continuacao(pergunta):
            return False
        conteudo = palavras(pergunta)
        if not conteudo:  # "E aí?", "E onde?": nada a comparar, mantém a continuação
            return True
        anterior = palavras(" ".join([self.historico[-2].conteudo, self.historico[-1].conteudo]
                                     + [t.texto for t in self._ultimo_contexto]))
        return compartilham_radical(conteudo, anterior)

    def perguntar(self, pergunta: str) -> str:
        if eh_emergencia(pergunta):
            return self._registrar(pergunta, MSG_EMERGENCIA, "emergencia", [])

        # Para continuação ("e onde eu faço isso?"), a busca usa também a pergunta anterior.
        consulta = pergunta
        if self._eh_continuacao(pergunta):
            consulta = f"{self.historico[-2].conteudo} {pergunta}"
        contexto = self.base.buscar(consulta, self.k)

        # Guarda de alucinação: sem nenhum trecho confiável, nem chama o LLM.
        if self.exigir_contexto and not contexto:
            return self._registrar(pergunta, MSG_SEM_CONTEXTO, "sem_contexto", [])

        recorte = (self.historico + [Mensagem("user", pergunta)])[-(2 * MAX_TURNOS_MEMORIA - 1):]
        resposta = self.llm.responder(SYSTEM_PROMPT, recorte, contexto).strip()
        return self._registrar(pergunta, resposta, "llm", contexto)

    def _registrar(self, pergunta: str, resposta: str, motivo: str, contexto: list[Trecho]) -> str:
        self.historico += [Mensagem("user", pergunta), Mensagem("assistant", resposta)]
        self.ultimo_motivo = motivo
        self._ultimo_contexto = contexto
        return resposta

    def limpar(self) -> None:
        self.historico.clear()
        self.ultimo_motivo = ""
        self._ultimo_contexto = []
