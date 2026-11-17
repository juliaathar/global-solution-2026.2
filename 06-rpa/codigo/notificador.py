"""Notificação simulada com retry e espera exponencial."""
import json
import logging
import time
import urllib.error
import urllib.request

import config

log = logging.getLogger("rpa.notificador")


class ErroNotificacao(Exception):
    pass


def enviar(protocolo: str) -> None:
    """Envia o protocolo à API do app (RPA_API_URL, ex.: http://localhost:8000/protocolos).

    Sem RPA_API_URL configurada, apenas simula o envio. Timeout curto; falha de rede
    vira ErroNotificacao e é tratada pelo retry.
    """
    if not config.API_URL:
        return None
    req = urllib.request.Request(
        config.API_URL, data=json.dumps({"protocolo": protocolo}).encode("utf-8"),
        headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=config.TIMEOUT_S):
            pass
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        raise ErroNotificacao(str(e)) from e


def enviar_com_retry(protocolo, tentativas, espera_base, enviar_fn=enviar) -> bool:
    for i in range(1, tentativas + 1):
        try:
            enviar_fn(protocolo)
            return True
        except ErroNotificacao as e:
            log.warning("Notificação %s falhou (tentativa %d/%d): %s", protocolo, i, tentativas, e)
            if i < tentativas:
                time.sleep(espera_base * 2 ** (i - 1))
    log.error("Notificação %s não enviada; segue sem notificar", protocolo)
    return False
