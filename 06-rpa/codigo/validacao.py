from config import TAMANHO_MAX, TAMANHO_MIN


def validar(relato: dict) -> tuple[bool, str]:
    texto = (relato.get("texto") or "").strip()
    if not relato.get("id"):
        return False, "id ausente"
    if not texto:
        return False, "texto vazio"
    if len(texto) < TAMANHO_MIN:
        return False, "texto curto demais"
    if len(texto) > TAMANHO_MAX:
        return False, "texto longo demais"
    return True, ""
