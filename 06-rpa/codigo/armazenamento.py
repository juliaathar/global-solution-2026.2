"""SQLite com protocolo idempotente: o mesmo relato nunca gera dois protocolos."""
import sqlite3
from datetime import datetime


class Armazenamento:
    def __init__(self, caminho):
        caminho.parent.mkdir(parents=True, exist_ok=True)
        self.con = sqlite3.connect(caminho)
        self.con.execute(
            """CREATE TABLE IF NOT EXISTS protocolos (
            relato_id TEXT PRIMARY KEY, protocolo TEXT, categoria TEXT,
            urgencia TEXT, confianca REAL, criado_em TEXT)"""
        )

    def existe(self, relato_id: str) -> bool:
        return self.con.execute("SELECT 1 FROM protocolos WHERE relato_id=?", (relato_id,)).fetchone() is not None

    def salvar(self, relato_id, categoria, urgencia, confianca) -> str:
        n = self.con.execute("SELECT COUNT(*) FROM protocolos").fetchone()[0] + 1
        protocolo = f"ACB-{datetime.now():%Y%m%d}-{n:05d}"
        self.con.execute(
            "INSERT INTO protocolos VALUES (?,?,?,?,?,?)",
            (relato_id, protocolo, categoria, urgencia, confianca, datetime.now().isoformat(timespec="seconds")),
        )
        self.con.commit()
        return protocolo

    def fechar(self):
        self.con.close()
