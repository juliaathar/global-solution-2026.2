from pydantic import BaseModel


class ResumoPainel(BaseModel):
    total: int
    abertos: int
    urgencia_alta: int
    para_revisao: int
    por_categoria: dict[str, int]
    por_regiao: dict[str, int]
    por_origem: dict[str, int]
    alertas_som_24h: int
