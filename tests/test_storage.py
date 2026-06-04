"""
Testes do M4 — Storage (SQLite).
Usam um banco temporário isolado. Cobrem criação, conteúdo,
fluxo de publicação e métricas.
"""
import tempfile
from pathlib import Path

import pytest

from src import config


@pytest.fixture
def db_temp(monkeypatch):
    tmp = Path(tempfile.mkdtemp())
    monkeypatch.setattr(config, "DB_PATH", tmp / "teste.db")
    from src.storage import db
    db.init_db()
    yield db


def test_salvar_e_listar_conteudo(db_temp):
    cid = db_temp.salvar_conteudo(
        plataforma="instagram", ideia="óleo de alecrim",
        legenda="legenda teste", hashtags="#eikovida", imagem_url="http://x/y.png")
    assert cid == 1
    lista = db_temp.listar_conteudo()
    assert len(lista) == 1
    assert lista[0]["plataforma"] == "instagram"
    assert lista[0]["status"] == "rascunho"


def test_fluxo_publicacao(db_temp):
    cid = db_temp.salvar_conteudo(plataforma="instagram", legenda="x")
    pid = db_temp.agendar_publicacao(cid, "instagram", agendado_para="2026-06-05T10:00")
    # aparece nas pendentes
    pendentes = db_temp.publicacoes_pendentes()
    assert len(pendentes) == 1
    assert pendentes[0]["id"] == pid
    # marca publicado -> sai das pendentes
    db_temp.marcar_publicado(pid, post_id_externo="EXT123")
    assert db_temp.publicacoes_pendentes() == []


def test_marcar_erro(db_temp):
    cid = db_temp.salvar_conteudo(plataforma="facebook", legenda="x")
    pid = db_temp.agendar_publicacao(cid, "facebook")
    db_temp.marcar_erro(pid, "token expirado")
    # não está mais pendente
    assert db_temp.publicacoes_pendentes() == []


def test_metricas_periodo(db_temp):
    cid = db_temp.salvar_conteudo(plataforma="instagram", legenda="x")
    pid = db_temp.agendar_publicacao(cid, "instagram")
    db_temp.salvar_metrica(pid, curtidas=10, comentarios=2, alcance=300)
    metricas = db_temp.metricas_periodo("2000-01-01T00:00")
    assert len(metricas) == 1
    assert metricas[0]["curtidas"] == 10
    assert metricas[0]["alcance"] == 300


def test_metricas_periodo_filtra_antigas(db_temp):
    cid = db_temp.salvar_conteudo(plataforma="instagram", legenda="x")
    pid = db_temp.agendar_publicacao(cid, "instagram")
    db_temp.salvar_metrica(pid, curtidas=5)
    # filtro no futuro não traz nada
    assert db_temp.metricas_periodo("2999-01-01T00:00") == []
