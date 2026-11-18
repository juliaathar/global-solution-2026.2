"""Registro das páginas (st.Page) para que uma página possa criar links para outra sem import circular."""
PAGINAS: dict = {}


def pagina(chave: str):
    return PAGINAS.get(chave)
