"""API simulada do app, só com a biblioteca padrão: serve para testar o POST do robô sem o front pronto.

Contrato que o `01-front-end/api` deve implementar para receber os protocolos do robô:

    POST /protocolos        Content-Type: application/json        corpo: {"protocolo": "ELB-20261117-00001"}
    201 -> {"recebido": "ELB-..."}            400 -> corpo que não é JSON ou sem "protocolo"
    GET  /protocolos        200 -> lista dos protocolos recebidos (só nesta simulação)

Uso: python api_simulada.py [porta]      (padrão 8000)  e, em outro terminal:
     RPA_API_URL=http://127.0.0.1:8000/protocolos python main.py
"""
import json
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

RECEBIDOS: list[dict] = []


class _Handler(BaseHTTPRequestHandler):
    def _responder(self, codigo: int, corpo: dict | list):
        dados = json.dumps(corpo, ensure_ascii=False).encode("utf-8")
        self.send_response(codigo)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(dados)))
        self.end_headers()
        self.wfile.write(dados)

    def do_POST(self):
        if self.path.rstrip("/") != "/protocolos":
            return self._responder(404, {"erro": "rota inexistente"})
        try:
            corpo = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"")
            protocolo = corpo["protocolo"]
            if not isinstance(protocolo, str) or not protocolo:
                raise ValueError
        except (ValueError, KeyError, TypeError):
            return self._responder(400, {"erro": "envie JSON com o campo 'protocolo'"})
        RECEBIDOS.append({"protocolo": protocolo})
        self._responder(201, {"recebido": protocolo})

    def do_GET(self):
        if self.path.rstrip("/") == "/protocolos":
            return self._responder(200, RECEBIDOS)
        self._responder(404, {"erro": "rota inexistente"})

    def log_message(self, *args):  # silencia o log padrão do http.server
        pass


def criar_servidor(porta: int = 8000) -> ThreadingHTTPServer:
    RECEBIDOS.clear()
    return ThreadingHTTPServer(("127.0.0.1", porta), _Handler)


if __name__ == "__main__":
    porta = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    srv = criar_servidor(porta)
    print(f"API simulada em http://127.0.0.1:{porta}/protocolos (Ctrl+C para parar)")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
