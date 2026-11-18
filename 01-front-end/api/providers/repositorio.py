"""Banco SQLite da API: ocorrências (protocolos com os dados do painel) e eventos sonoros do IoT.

Guarda apenas o texto já mascarado pela pasta 06. Áudio e foto do cidadão nunca são gravados.
"""
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta

from api.core import config

ESQUEMA = """
CREATE TABLE IF NOT EXISTS ocorrencias (
    protocolo TEXT PRIMARY KEY, origem TEXT, canal TEXT, categoria TEXT, urgencia TEXT,
    confianca REAL, regiao TEXT, status TEXT, metodo TEXT, resumo TEXT, texto_mascarado TEXT,
    criado_em TEXT, probabilidade_fissura REAL, alerta_inmet TEXT DEFAULT '', corrigido INTEGER DEFAULT 0);
CREATE TABLE IF NOT EXISTS eventos_som (
    id INTEGER PRIMARY KEY AUTOINCREMENT, classe TEXT, confianca REAL, dispositivo TEXT,
    virou_alerta INTEGER, motivo TEXT, criado_em TEXT);
"""
COLUNAS = ("protocolo", "origem", "canal", "categoria", "urgencia", "confianca", "regiao", "status", "metodo",
           "resumo", "criado_em", "probabilidade_fissura", "alerta_inmet")


def agora() -> str:
    return datetime.now().isoformat(timespec="seconds")


@contextmanager
def conexao():
    config.DADOS_DIR.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(config.BANCO_APP)
    con.row_factory = sqlite3.Row
    try:
        con.executescript(ESQUEMA)
        yield con
        con.commit()
    finally:
        con.close()


def salvar_ocorrencia(**campos) -> bool:
    """Insere; devolve False se o protocolo já existia (nada é sobrescrito)."""
    campos.setdefault("criado_em", agora())
    nomes = ",".join(campos)
    marcas = ",".join("?" * len(campos))
    with conexao() as con:
        cur = con.execute(f"INSERT OR IGNORE INTO ocorrencias ({nomes}) VALUES ({marcas})", tuple(campos.values()))
        return cur.rowcount == 1


def completar_ocorrencia(protocolo: str, **campos) -> None:
    """Preenche campos vazios de um protocolo já existente (o robô às vezes manda só o número)."""
    with conexao() as con:
        for k, v in campos.items():
            if v is not None and k in COLUNAS:  # só colunas conhecidas entram no SQL
                con.execute(f"UPDATE ocorrencias SET {k}=? WHERE protocolo=? AND ({k} IS NULL OR {k}='')",
                            (v, protocolo))


def listar_ocorrencias(categoria=None, urgencia=None, regiao=None, origem=None, status=None,
                       limite: int = 500) -> list[dict]:
    filtros, valores = [], []
    for col, val in (("categoria", categoria), ("urgencia", urgencia), ("regiao", regiao),
                     ("origem", origem), ("status", status)):
        if val:
            filtros.append(f"{col}=?")
            valores.append(val)
    where = f"WHERE {' AND '.join(filtros)}" if filtros else ""
    with conexao() as con:
        linhas = con.execute(f"SELECT {','.join(COLUNAS)} FROM ocorrencias {where} "
                             "ORDER BY criado_em DESC LIMIT ?", (*valores, limite)).fetchall()
    return [dict(l) for l in linhas]


def textos_recentes(categoria: str, regiao: str, dias: int = 30) -> list[tuple[str, str]]:
    """Relatos em aberto do mesmo assunto e da mesma região, candidatos a duplicado."""
    corte = (datetime.now() - timedelta(days=dias)).isoformat(timespec="seconds")
    with conexao() as con:
        return [(l["protocolo"], l["texto_mascarado"]) for l in con.execute(
            "SELECT protocolo, texto_mascarado FROM ocorrencias WHERE texto_mascarado IS NOT NULL "
            "AND status != 'resolvido' AND categoria = ? AND regiao = ? AND criado_em >= ?",
            (categoria, regiao, corte))]


def atualizar_status(protocolo: str, status: str) -> bool:
    with conexao() as con:
        return con.execute("UPDATE ocorrencias SET status=? WHERE protocolo=?", (status, protocolo)).rowcount == 1


def salvar_evento_som(classe: str, confianca: float, dispositivo: str, virou_alerta: bool, motivo: str) -> dict:
    criado = agora()
    with conexao() as con:
        cur = con.execute("INSERT INTO eventos_som (classe, confianca, dispositivo, virou_alerta, motivo, criado_em) "
                          "VALUES (?,?,?,?,?,?)", (classe, confianca, dispositivo, int(virou_alerta), motivo, criado))
        return {"id": cur.lastrowid, "criado_em": criado}


def listar_eventos_som(limite: int = 100, so_alertas: bool = False) -> list[dict]:
    where = "WHERE virou_alerta=1" if so_alertas else ""
    with conexao() as con:
        linhas = con.execute(f"SELECT * FROM eventos_som {where} ORDER BY id DESC LIMIT ?", (limite,)).fetchall()
    return [{**dict(l), "virou_alerta": bool(l["virou_alerta"])} for l in linhas]


def contar_alertas_som(horas: int = 24) -> int:
    corte = (datetime.now() - timedelta(hours=horas)).isoformat(timespec="seconds")
    with conexao() as con:
        return con.execute("SELECT COUNT(*) FROM eventos_som WHERE virou_alerta=1 AND criado_em >= ?",
                           (corte,)).fetchone()[0]
