"""Base de conhecimento real: adaptador do motor RAG da pasta 03-generative-ai.

Usa só a recuperação do 03 (chunking por seção, embeddings e5-large, top-k) e as proteções que
valem para a busca: abstenção por evidência fraca, pedido malicioso, pergunta vaga e neutralização
de instruções escondidas nos trechos. O LLM, a memória e as guardas de emergência continuam sendo
os da voz (`llm/assistente.py`).

Quando não há evidência confiável, `buscar` devolve lista vazia e o assistente cai na guarda
"sem contexto" (resposta fixa, sem chamar o LLM).
"""
import sys
from pathlib import Path

from interfaces import Trecho

PASTA_03 = Path(__file__).resolve().parents[2] / "03-generative-ai"


def _importar_03():
    if str(PASTA_03) not in sys.path:
        sys.path.append(str(PASTA_03))  # no fim: não sobrepõe módulos do 02 (config, llm...)
    from rag import motor
    from rag.seguranca import filtros
    return motor, filtros


class BaseRAG:
    def __init__(self):
        self._motor, self._filtros = _importar_03()
        self._motor.indice()  # carrega ou constrói o índice agora, não na primeira pergunta

    def buscar(self, pergunta: str, k: int = 3) -> list[Trecho]:
        f = self._filtros
        if f.pedido_malicioso(pergunta) or f.pergunta_vaga(pergunta, False):
            return []
        trechos = self._motor.indice().buscar(pergunta, k)
        if f.evidencia_fraca(trechos):
            return []
        resultado = []
        for t in trechos:
            texto, _ = f.neutralizar_contexto(t["texto"])
            resultado.append(Trecho(texto, f"{t['titulo']}, consultado em {t['data_consulta']}"))
        return resultado
