"""
Camada de persistência (SQLite puro, sem ORM).
Guarda o conteúdo gerado, a fila de publicações e as métricas.
Banco fica num único arquivo, versionado no repositório.
"""
import sqlite3
from datetime import datetime, timezone

from src import config


def _agora() -> str:
    return datetime.now(timezone.utc).isoformat()

SCHEMA = """
CREATE TABLE IF NOT EXISTS conteudo (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    criado_em    TEXT NOT NULL,
    plataforma   TEXT NOT NULL,
    ideia        TEXT,
    legenda      TEXT,
    hashtags     TEXT,
    prompt_imagem TEXT,
    imagem_url   TEXT,
    status       TEXT NOT NULL DEFAULT 'rascunho'
);

CREATE TABLE IF NOT EXISTS publicacoes (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    conteudo_id   INTEGER NOT NULL REFERENCES conteudo(id),
    plataforma    TEXT NOT NULL,
    agendado_para TEXT,
    publicado_em  TEXT,
    post_id_externo TEXT,
    status        TEXT NOT NULL DEFAULT 'pendente',
    erro          TEXT
);

CREATE TABLE IF NOT EXISTS metricas (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    publicacao_id INTEGER NOT NULL REFERENCES publicacoes(id),
    curtidas     INTEGER DEFAULT 0,
    comentarios  INTEGER DEFAULT 0,
    alcance      INTEGER DEFAULT 0,
    coletado_em  TEXT NOT NULL
);
"""


def get_conn():
    conn = sqlite3.connect(str(config.DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    with get_conn() as conn:
        conn.executescript(SCHEMA)


# ---------- Conteúdo ----------
def salvar_conteudo(plataforma, ideia="", legenda="", hashtags="",
                    prompt_imagem="", imagem_url="", status="rascunho") -> int:
    with get_conn() as conn:
        cur = conn.execute(
            """INSERT INTO conteudo (criado_em, plataforma, ideia, legenda, hashtags,
                                     prompt_imagem, imagem_url, status)
               VALUES (?,?,?,?,?,?,?,?)""",
            (_agora(), plataforma, ideia, legenda, hashtags,
             prompt_imagem, imagem_url, status),
        )
        return cur.lastrowid


def listar_conteudo(limite=50) -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM conteudo ORDER BY id DESC LIMIT ?", (limite,)
        ).fetchall()
        return [dict(r) for r in rows]


def obter_conteudo(conteudo_id) -> dict | None:
    """Busca um conteúdo específico por id (usado pelo publicador no M5)."""
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM conteudo WHERE id = ?", (conteudo_id,)
        ).fetchone()
        return dict(row) if row else None


# ---------- Publicações ----------
def agendar_publicacao(conteudo_id, plataforma, agendado_para=None) -> int:
    with get_conn() as conn:
        cur = conn.execute(
            """INSERT INTO publicacoes (conteudo_id, plataforma, agendado_para, status)
               VALUES (?,?,?, 'pendente')""",
            (conteudo_id, plataforma, agendado_para),
        )
        return cur.lastrowid


def publicacoes_pendentes() -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM publicacoes WHERE status = 'pendente' ORDER BY id"
        ).fetchall()
        return [dict(r) for r in rows]


def publicacoes_publicadas(desde_iso: str) -> list[dict]:
    """Publicações já postadas a partir de uma data (usado pelo relatório semanal)."""
    with get_conn() as conn:
        rows = conn.execute(
            """SELECT * FROM publicacoes
               WHERE status='publicado' AND publicado_em >= ?
               ORDER BY publicado_em""",
            (desde_iso,),
        ).fetchall()
        return [dict(r) for r in rows]


def marcar_publicado(publicacao_id, post_id_externo):
    with get_conn() as conn:
        conn.execute(
            """UPDATE publicacoes
               SET status='publicado', publicado_em=?, post_id_externo=?, erro=NULL
               WHERE id=?""",
            (_agora(), post_id_externo, publicacao_id),
        )


def marcar_erro(publicacao_id, erro):
    with get_conn() as conn:
        conn.execute(
            "UPDATE publicacoes SET status='erro', erro=? WHERE id=?",
            (str(erro), publicacao_id),
        )


# ---------- Métricas ----------
def salvar_metrica(publicacao_id, curtidas=0, comentarios=0, alcance=0):
    with get_conn() as conn:
        conn.execute(
            """INSERT INTO metricas (publicacao_id, curtidas, comentarios, alcance, coletado_em)
               VALUES (?,?,?,?,?)""",
            (publicacao_id, curtidas, comentarios, alcance, _agora()),
        )


def metricas_periodo(desde_iso: str) -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM metricas WHERE coletado_em >= ? ORDER BY coletado_em",
            (desde_iso,),
        ).fetchall()
        return [dict(r) for r in rows]
