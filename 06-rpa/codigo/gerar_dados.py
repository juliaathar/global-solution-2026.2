"""Gera relatos sintéticos rotulados (sem dados pessoais reais)."""
import csv
import random
import sys
from pathlib import Path

PROBLEMAS = {
    ("buraco", "alta"): ["buraco enorme que já causou acidente", "buraco perigoso, carros desviam na contramão", "cratera no asfalto com risco para motos"],
    ("buraco", "media"): ["buraco no asfalto atrapalhando o trânsito", "pista esburacada", "asfalto afundando aos poucos"],
    ("iluminacao", "media"): ["poste apagado há duas semanas", "rua sem iluminação à noite", "lâmpada queimada no poste da esquina", "escuridão total depois das 18h"],
    ("lixo", "baixa"): ["lixo acumulado na esquina", "entulho largado há dias", "sujeira espalhada na calçada do mercado", "caçamba cheia transbordando"],
    ("calcada", "media"): ["calçada quebrada que dificulta cadeirante", "calçada com rachadura grande", "piso da calçada solto e desnivelado"],
    ("alagamento", "alta"): ["alagamento depois da chuva, água entrando nas casas", "bueiro entupido causando alagamento", "enchente na rua, risco para moradores"],
    ("servico_saude", "media"): ["onde fica a UBS mais próxima?", "como marcar consulta no posto de saúde?", "onde tomar vacina perto daqui?", "como conseguir atendimento médico gratuito?"],
}
ABERTURAS = ["", "Bom dia. ", "Pessoal, ", "Gostaria de informar: ", "Atenção: ", "Moro aqui e queria avisar que "]
RUAS = ["Rua das Flores", "Av. Brasil", "Rua do Comércio", "Rua Sete", "Av. Central", "Rua da Paz", "Rua Bela Vista", "Travessa Sol", "Rua do Mercado", "Av. das Palmeiras"]
FECHOS = ["", " Já faz tempo.", " Por favor, enviem alguém.", " Preciso de uma solução.", " Isso afeta muita gente."]


SAUDE_COM_UBS = ["onde fica a UBS do {b}?", "como marcar consulta na UBS {b}?", "a UBS {b} abre aos sábados?",
                 "qual o horário de vacina na UBS {b}?", "preciso de atendimento na unidade de saúde do {b}"]


def _unidades_reais():
    """Nomes de bairros das UBS reais de SJC (do snapshot da página pública), para relatos de saúde realistas."""
    from coleta_web import extrair_css
    import config
    return [u["nome"].removeprefix("UBS ").strip() for u in extrair_css(config.UBS_SNAPSHOT.read_text(encoding="utf-8"))]


def gerar(n=120, semente=42):
    rnd = random.Random(semente)
    linhas = []
    chaves = list(PROBLEMAS)
    bairros = _unidades_reais()
    for i in range(n):
        cat, urg = rnd.choice(chaves)
        ubs_real = ""
        if cat == "servico_saude" and rnd.random() < 0.6:  # relato que cita a unidade pelo bairro
            ubs_real = rnd.choice(bairros)
            txt = rnd.choice(ABERTURAS) + rnd.choice(SAUDE_COM_UBS).format(b=ubs_real) + rnd.choice(FECHOS)
        else:
            prob = rnd.choice(PROBLEMAS[(cat, urg)])
            rua = f"{rnd.choice(RUAS)}, {rnd.randint(1, 999)}"
            txt = f"{rnd.choice(ABERTURAS)}{prob} na {rua}.{rnd.choice(FECHOS)}"
        txt = txt[0].upper() + txt[1:]
        linhas.append({"id": f"R{i:04d}", "texto": txt, "categoria_real": cat, "urgencia_real": urg,
                       "ubs_real": f"UBS {ubs_real}" if ubs_real else ""})
    # casos problemáticos: duplicado, vazio, curto, longo demais, ambíguo
    linhas.append({**linhas[0], "id": "R9001"})
    linhas.append({"id": "R9002", "texto": "", "categoria_real": "", "urgencia_real": "", "ubs_real": ""})
    linhas.append({"id": "R9003", "texto": "oi", "categoria_real": "", "urgencia_real": "", "ubs_real": ""})
    linhas.append({"id": "R9004", "texto": "x" * 800, "categoria_real": "", "urgencia_real": "", "ubs_real": ""})
    linhas.append({"id": "R9005", "texto": "Preciso de ajuda com uma coisa que não sei explicar direito", "categoria_real": "indefinido", "urgencia_real": "baixa", "ubs_real": ""})
    return linhas


if __name__ == "__main__":
    padrao = Path(__file__).resolve().parent.parent / "dados_sinteticos" / "relatos.csv"
    destino = Path(sys.argv[1]) if len(sys.argv) > 1 else padrao
    destino.parent.mkdir(parents=True, exist_ok=True)
    with open(destino, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["id", "texto", "categoria_real", "urgencia_real", "ubs_real"])
        w.writeheader()
        w.writerows(gerar())
    print(f"Gerado: {destino}")
