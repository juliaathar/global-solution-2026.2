"""Enriquecimento do relato com fontes web, consultadas só quando o relato precisa delas (preguiçoso)."""
import config
from coleta_inmet import coletar_avisos
from coleta_web import coletar_ubs, sugerir_ubs

SEVERIDADES = ("Perigo Potencial", "Perigo", "Grande Perigo")


class Enriquecedor:
    def __init__(self, resumo: dict):
        self.resumo = resumo
        self._ubs = None
        self._avisos = None

    def aviso_inmet(self, classificacao: dict) -> str:
        """Texto do pior aviso vigente para relato de alagamento, ou '' se não houver."""
        if classificacao["categoria"] != "alagamento":
            return ""
        if self._avisos is None:
            self._avisos, self.resumo["inmet_origem"] = coletar_avisos()
            self.resumo["avisos_vigentes"] = len(self._avisos)
        if not self._avisos:
            return ""
        pior = max(self._avisos, key=lambda a: SEVERIDADES.index(a["severidade"]) if a["severidade"] in SEVERIDADES else -1)
        return f"Inmet: {pior['evento']} ({pior['severidade']}) em {config.INMET_AREA}"

    def encaminhamento(self, texto: str, classificacao: dict) -> str:
        """UBS sugerida para relato de saúde, ou '' para as demais categorias."""
        if classificacao["categoria"] != "servico_saude":
            return ""
        if self._ubs is None:
            self._ubs, self.resumo["ubs_origem"] = coletar_ubs()
        u = sugerir_ubs(texto, self._ubs)
        return f"{u['nome']} - {u['endereco']} - {u['horario']}" if u else "Consulte a lista de UBS da prefeitura"
