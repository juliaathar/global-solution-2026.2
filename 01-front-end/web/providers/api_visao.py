import os

import requests

API_URL = os.getenv("API_URL", "http://localhost:8000")


class ErroAPI(Exception):
    pass


def _post(caminho: str, arquivo, params: dict, timeout: int):
    try:
        r = requests.post(f"{API_URL}{caminho}", files={"arquivo": (arquivo.name, arquivo.getvalue(), arquivo.type)},
                          params=params, timeout=timeout)
    except requests.ConnectionError:
        raise ErroAPI("Não foi possível conectar à API. Verifique se ela está no ar.")
    except requests.Timeout:
        raise ErroAPI("A API demorou demais para responder. Tente um arquivo menor.")
    if r.status_code != 200:
        try:
            detalhe = r.json().get("detail", r.text)
        except ValueError:
            detalhe = r.text
        raise ErroAPI(f"Erro {r.status_code}: {detalhe}")
    try:
        return r.json()
    except ValueError:
        raise ErroAPI("Resposta inválida da API.")


def classificar_imagem(arquivo, limiar: float) -> dict:
    return _post("/visao/imagem", arquivo, {"limiar": limiar}, timeout=30)


def classificar_video(arquivo, passo: int, limiar: float) -> dict:
    return _post("/visao/video", arquivo, {"passo": passo, "limiar": limiar}, timeout=180)
