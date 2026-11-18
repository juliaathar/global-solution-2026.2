"""Provedores de LLM: Ollama (local) e APIs compatíveis com OpenAI (OpenAI, Gemini, Groq)."""
import os

import requests

from interfaces import Mensagem, Trecho

URLS_OPENAI = {
    "openai": "https://api.openai.com/v1/chat/completions",
    "groq": "https://api.groq.com/openai/v1/chat/completions",
    "gemini": "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
}


def _mensagens(system: str, historico: list[Mensagem], contexto: list[Trecho]) -> list[dict]:
    ctx = "\n".join(f"- {t.texto} (fonte: {t.fonte})" for t in contexto) or "(nenhuma informação encontrada)"
    msgs = [{"role": "system", "content": f"{system}\n\nContexto:\n{ctx}"}]
    msgs += [{"role": m.papel, "content": m.conteudo} for m in historico]
    return msgs


class OllamaLLM:
    def __init__(self, modelo: str, url: str = "http://localhost:11434"):
        self.nome, self.url = f"ollama/{modelo}", url
        self.modelo = modelo

    def responder(self, system, historico, contexto) -> str:
        r = requests.post(f"{self.url}/api/chat", timeout=120, json={
            "model": self.modelo, "stream": False,
            "options": {"temperature": 0.2},
            "messages": _mensagens(system, historico, contexto)})
        r.raise_for_status()
        return r.json()["message"]["content"]


class OpenAICompatLLM:
    def __init__(self, provedor: str, modelo: str, api_key: str):
        self.nome = f"{provedor}/{modelo}"
        self.url, self.modelo, self.api_key = URLS_OPENAI[provedor], modelo, api_key

    def responder(self, system, historico, contexto) -> str:
        r = requests.post(self.url, timeout=60, headers={"Authorization": f"Bearer {self.api_key}"},
                          json={"model": self.modelo, "temperature": 0.2,
                                "messages": _mensagens(system, historico, contexto)})
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]


def criar_llm(provedor: str, modelo: str, api_key: str = ""):
    if provedor == "ollama":
        return OllamaLLM(modelo, os.getenv("OLLAMA_URL", "http://localhost:11434"))
    if provedor not in URLS_OPENAI:
        raise ValueError(f"LLM_PROVIDER desconhecido: {provedor!r} (use ollama, openai, groq ou gemini)")
    return OpenAICompatLLM(provedor, modelo, api_key)
