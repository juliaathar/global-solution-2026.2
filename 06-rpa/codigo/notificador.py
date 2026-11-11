"""Notificação simulada com retry e espera exponencial."""
import logging
import time

log = logging.getLogger("rpa.notificador")


class ErroNotificacao(Exception):
    pass


def enviar(protocolo: str) -> None:
    """Simula o envio ao cidadão ou ao gestor. Troque por e-mail ou webhook real."""
    return None


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
