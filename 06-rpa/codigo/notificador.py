"""Notificação com retry e espera exponencial: API do app e e-mail (SMTP)."""
import json
import logging
import smtplib
import time
import urllib.error
import urllib.request
from email.message import EmailMessage

import config

log = logging.getLogger("rpa.notificador")


class ErroNotificacao(Exception):
    pass


class ErroNotificacaoPermanente(ErroNotificacao):
    """Falha que repetir não resolve (ex.: senha SMTP recusada). O retry desiste na hora."""


_entregues: set[tuple[str, str]] = set()  # (canal, protocolo): no retry não reenvia o que já foi entregue


def _enviar_api(protocolo: str) -> None:
    req = urllib.request.Request(
        config.API_URL, data=json.dumps({"protocolo": protocolo}).encode("utf-8"),
        headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=config.TIMEOUT_S):
            pass
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        raise ErroNotificacao(f"API: {e}") from e


def montar_email(protocolo: str, dados: dict) -> EmailMessage:
    """E-mail ao gestor. Leva protocolo, categoria, urgência e encaminhamento; nunca o texto do cidadão."""
    msg = EmailMessage()
    msg["Subject"] = f"[EloBairro] Protocolo {protocolo} ({dados.get('urgencia', '?')})"
    msg["From"] = config.SMTP_USUARIO
    msg["To"] = config.EMAIL_DESTINO
    linhas = [f"Protocolo: {protocolo}", f"Categoria: {dados.get('categoria', '')}",
              f"Urgência: {dados.get('urgencia', '')}", f"Confiança: {dados.get('confianca', '')}"]
    if dados.get("alerta_inmet"):
        linhas.append(f"Alerta: {dados['alerta_inmet']}")
    if dados.get("encaminhamento"):
        linhas.append(f"Encaminhamento: {dados['encaminhamento']}")
    msg.set_content("\n".join(linhas) + "\n\nMensagem automática do robô RPA do EloBairro.")
    return msg


def _enviar_email(protocolo: str, dados: dict) -> None:
    msg = montar_email(protocolo, dados)
    try:
        with smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORTA, timeout=config.TIMEOUT_S) as servidor:
            servidor.starttls()
            servidor.login(config.SMTP_USUARIO, config.SMTP_SENHA)
            servidor.send_message(msg)
    except smtplib.SMTPAuthenticationError as e:
        raise ErroNotificacaoPermanente(f"e-mail: autenticação recusada ({e.smtp_code})") from e
    except (smtplib.SMTPException, OSError) as e:
        raise ErroNotificacao(f"e-mail: {e}") from e  # a senha nunca entra na mensagem de erro


def enviar(protocolo: str, dados: dict | None = None) -> None:
    """Notifica pelos canais ligados: API do app (RPA_API_URL) e e-mail (se SMTP configurado e urgência listada).

    Sem nenhum canal, apenas simula. Um canal que falha não impede o outro; o erro sobe para o retry,
    que não reenvia o canal já entregue.
    """
    canais = []
    if config.API_URL:
        canais.append(("api", lambda: _enviar_api(protocolo)))
    if config.EMAIL_ATIVO and dados is not None and dados.get("urgencia") in config.EMAIL_URGENCIAS:
        canais.append(("email", lambda: _enviar_email(protocolo, dados)))
    erros = []
    for nome, fn in canais:
        if (nome, protocolo) in _entregues:
            continue
        try:
            fn()
            _entregues.add((nome, protocolo))
        except ErroNotificacao as e:
            erros.append(e)
    if erros:
        permanente = all(isinstance(e, ErroNotificacaoPermanente) for e in erros)
        raise (ErroNotificacaoPermanente if permanente else ErroNotificacao)("; ".join(str(e) for e in erros))


def enviar_com_retry(protocolo, tentativas, espera_base, enviar_fn=enviar, dados=None) -> bool:
    for i in range(1, tentativas + 1):
        try:
            enviar_fn(protocolo) if dados is None else enviar_fn(protocolo, dados)
            return True
        except ErroNotificacaoPermanente as e:
            log.error("Notificação %s falhou sem chance de retry: %s", protocolo, e)
            return False
        except ErroNotificacao as e:
            log.warning("Notificação %s falhou (tentativa %d/%d): %s", protocolo, i, tentativas, e)
            if i < tentativas:
                time.sleep(espera_base * 2 ** (i - 1))
    log.error("Notificação %s não enviada; segue sem notificar", protocolo)
    return False
