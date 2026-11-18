from collections import Counter

from fastapi import APIRouter

from api.providers import repositorio
from api.schemas.painel import ResumoPainel

router = APIRouter(prefix="/painel", tags=["painel"])


@router.get("/resumo", response_model=ResumoPainel)
def resumo():
    oc = repositorio.listar_ocorrencias(limite=5000)
    return ResumoPainel(
        total=len(oc),
        abertos=sum(o["status"] != "resolvido" for o in oc),
        urgencia_alta=sum(o["urgencia"] == "alta" and o["status"] != "resolvido" for o in oc),
        para_revisao=sum(o["status"] == "em_analise" for o in oc),
        por_categoria=dict(Counter(o["categoria"] for o in oc)),
        por_regiao=dict(Counter(o["regiao"] for o in oc)),
        por_origem=dict(Counter(o["origem"] for o in oc)),
        alertas_som_24h=repositorio.contar_alertas_som(24),
    )
