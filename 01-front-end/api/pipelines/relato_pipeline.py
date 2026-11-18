"""Relato do cidadão: proposta da IA (analisar) e registro só depois da confirmação humana (confirmar).

analisar:  texto -> máscara de dados pessoais (06) -> LLM com saída validada (Pydantic)
           -> se o LLM falhar ou responder fora do formato, classificador por regras (06)
           -> foto com fissura (04) reforça a categoria calçada -> verificação de duplicado
confirmar: grava no banco de protocolos do robô (06) e no banco do painel. Nada é gravado sem o "sim".
"""
import logging
import re
import uuid

from api.core import config
from api.providers import llm_provider, repositorio, rpa_provider
from api.schemas.relato import ConfirmacaoRelato, PropostaRelato, ProtocoloCriado, RelatoEntrada

log = logging.getLogger("elobairro.relatos")

ROTULOS = {
    "buraco": "Buraco na rua", "iluminacao": "Iluminação pública", "lixo": "Lixo e entulho",
    "calcada": "Calçada danificada", "alagamento": "Alagamento ou bueiro", "servico_saude": "Serviço de saúde",
    "indefinido": "Outro assunto",
}
# Para onde o pedido vai. Sem prazos inventados: a prefeitura informa o prazo no atendimento.
ENCAMINHAMENTOS = {
    "buraco": "Manutenção da Cidade (tapa-buracos). Acompanhe pelo 156.",
    "iluminacao": "Manutenção da Cidade (iluminação pública). Acompanhe pelo 156.",
    "lixo": "Manutenção da Cidade (limpeza e coleta). Acompanhe pelo 156.",
    "calcada": "Mobilidade Urbana e Manutenção da Cidade. Acompanhe pelo 156.",
    "alagamento": "Manutenção da Cidade (bueiros e drenagem). Se a água estiver entrando em casa, ligue 199 (Defesa Civil).",
    "servico_saude": "Secretaria de Saúde. Use a aba Perguntar para saber a UBS e o horário. Em emergência, ligue 192.",
    "indefinido": "Uma pessoa da equipe vai ler o seu relato e encaminhar. Você também pode ligar 156.",
}
PROXIMO_PASSO = {
    "alta": "Seu pedido entrou como prioridade. Guarde o número do protocolo.",
    "media": "Seu pedido entrou na fila da equipe responsável. Guarde o número do protocolo.",
    "baixa": "Seu pedido foi registrado. Guarde o número do protocolo para acompanhar.",
}


def _numeros(texto: str) -> set[str]:
    return set(re.findall(r"\d+", texto))


def _duplicado(texto_mascarado: str, categoria: str, regiao: str) -> str | None:
    """Mesmo assunto, mesma região, mesmos números (ex.: o número da casa) e texto muito parecido.

    Só a similaridade não basta: "poste apagado na Rua A, 10" e "poste apagado na Rua B, 88" são quase
    iguais letra a letra, mas são dois problemas. Exigir os mesmos números evita juntar endereços diferentes.
    """
    melhor, prot = 0.0, None
    for protocolo, texto in repositorio.textos_recentes(categoria, regiao):
        if _numeros(texto) != _numeros(texto_mascarado):
            continue
        s = rpa_provider.similaridade(texto_mascarado, texto)
        if s > melhor:
            melhor, prot = s, protocolo
    return prot if melhor >= config.SIMILARIDADE_DUPLICADO else None


def analisar(entrada: RelatoEntrada) -> PropostaRelato:
    texto, n_mascarados = rpa_provider.mascarar(entrada.texto)  # daqui em diante só o texto mascarado
    regras = rpa_provider.classificar(texto)
    avisos: list[str] = []
    if n_mascarados:
        avisos.append(f"Tiramos {n_mascarados} dado(s) pessoal(is) do texto (telefone, CPF, e-mail ou nome).")

    try:
        llm = llm_provider.estruturar(texto)
        categoria, urgencia, resumo, metodo = llm.categoria, llm.urgencia, llm.resumo, "llm"
        # Confiança: concordância entre o LLM e as regras do robô (o LLM não dá probabilidade calibrada)
        concorda = llm.categoria == regras["categoria"]
        confianca = 0.9 if concorda else 0.6
        if urgencia == "baixa" and regras["urgencia"] == "alta":
            urgencia = "alta"  # na dúvida sobre risco, a regra de segurança vence
            avisos.append("Mantivemos urgência alta porque o texto fala de risco.")
    except llm_provider.ErroLLM as e:
        log.warning("LLM indisponível, usando regras: %s", e)
        categoria, urgencia, confianca, metodo = regras["categoria"], regras["urgencia"], regras["confianca"], "regras"
        resumo = texto if len(texto) <= 160 else texto[:157] + "..."
        if llm_provider.disponivel():
            avisos.append("O assistente inteligente não respondeu; usamos a classificação automática simples.")

    if entrada.foto and entrada.foto.inspecao_recomendada:
        if categoria in ("indefinido", "calcada"):
            categoria = "calcada"
            confianca = max(confianca, 0.75)
        avisos.append(f"A foto mostra possível fissura ({entrada.foto.probabilidade_fissura:.0%}). "
                      "É só triagem: uma pessoa vai avaliar o local.")

    precisa_revisao = categoria == "indefinido" or confianca < config.CONFIANCA_REVISAO
    if precisa_revisao:
        avisos.append("Não temos certeza da categoria. Confira e corrija antes de confirmar.")
    return PropostaRelato(
        texto_mascarado=texto, dados_pessoais_mascarados=n_mascarados, categoria=categoria,
        categoria_rotulo=ROTULOS[categoria], urgencia=urgencia, confianca=round(confianca, 2), resumo=resumo,
        encaminhamento=ENCAMINHAMENTOS[categoria], metodo=metodo, precisa_revisao=precisa_revisao,
        avisos=avisos, regiao=entrada.regiao, origem=entrada.origem,
        duplicado_de=_duplicado(texto, categoria, entrada.regiao))


def confirmar(c: ConfirmacaoRelato) -> ProtocoloCriado:
    # Mascara de novo: o texto volta do navegador e não pode ser confiado só porque já passou pela máscara
    texto, _ = rpa_provider.mascarar(c.texto_mascarado)
    existente = _duplicado(texto, c.categoria, c.regiao)
    if existente:
        return ProtocoloCriado(protocolo=existente, novo=False, categoria_rotulo=ROTULOS[c.categoria],
                               urgencia=c.urgencia, encaminhamento=ENCAMINHAMENTOS[c.categoria],
                               proximo_passo="Esse problema já foi registrado. Juntamos o seu aviso ao protocolo existente.",
                               status="aberto")
    status = "em_analise" if c.categoria == "indefinido" or c.confianca < config.CONFIANCA_REVISAO else "aberto"
    protocolo, _ = rpa_provider.gerar_protocolo(f"APP-{uuid.uuid4().hex[:12]}", c.categoria, c.urgencia, c.confianca)
    repositorio.salvar_ocorrencia(
        protocolo=protocolo, origem="app", canal=c.origem, categoria=c.categoria, urgencia=c.urgencia,
        confianca=c.confianca, regiao=c.regiao, status=status,
        metodo=f"{c.metodo}+correcao_cidadao" if c.corrigido_pelo_cidadao else c.metodo,
        resumo=texto[:160], texto_mascarado=texto, probabilidade_fissura=c.probabilidade_fissura,
        corrigido=int(c.corrigido_pelo_cidadao))
    log.info("Protocolo %s criado (categoria=%s, urgencia=%s)", protocolo, c.categoria, c.urgencia)
    return ProtocoloCriado(protocolo=protocolo, novo=True, categoria_rotulo=ROTULOS[c.categoria], urgencia=c.urgencia,
                           encaminhamento=ENCAMINHAMENTOS[c.categoria], proximo_passo=PROXIMO_PASSO[c.urgencia],
                           status=status)
