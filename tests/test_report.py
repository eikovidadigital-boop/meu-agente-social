"""
Testes do M7 — Relatório Semanal.
Usam coletor falso e vault/banco temporários.
Cobrem coleta de métricas, geração do markdown e salvamento no vault.
"""
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import pytest

from src import config


class FakeCollector:
    def coletar(self, post_id_externo, plataforma="instagram"):
        return {"curtidas": 10, "comentarios": 3, "alcance": 200}


@pytest.fixture
def ambiente(monkeypatch):
    tmp = Path(tempfile.mkdtemp())
    vault = tmp / "vault"; vault.mkdir()
    monkeypatch.setattr(config, "VAULT_DIR", vault)
    monkeypatch.setattr(config, "DB_PATH", tmp / "teste.db")
    from src.storage import db
    db.init_db()
    yield db, vault
    shutil.rmtree(tmp, ignore_errors=True)


def test_coleta_metricas_dos_publicados(ambiente):
    db, _ = ambiente
    from src.report import weekly
    # cria conteúdo + publicação publicada
    cid = db.salvar_conteudo(plataforma="instagram", legenda="x")
    pid = db.agendar_publicacao(cid, "instagram")
    db.marcar_publicado(pid, "EXT1")

    n = weekly.coletar_metricas(FakeCollector(), dias=7)
    assert n == 1
    metricas = db.metricas_periodo("2000-01-01T00:00")
    assert len(metricas) == 1
    assert metricas[0]["curtidas"] == 10
    assert metricas[0]["alcance"] == 200


def test_gera_relatorio_com_totais(ambiente):
    db, vault = ambiente
    from src.report import weekly
    cid = db.salvar_conteudo(plataforma="instagram", legenda="x")
    pid = db.agendar_publicacao(cid, "instagram")
    db.marcar_publicado(pid, "EXT1")
    weekly.coletar_metricas(FakeCollector(), dias=7)

    md = weekly.gerar_relatorio(dias=7, salvar=True)
    assert "Relatório Semanal" in md
    assert "Curtidas totais: **10**" in md
    assert "Alcance total: **200**" in md
    # salvou no vault
    relatorios = list((vault / "Relatorios").glob("*.md"))
    assert len(relatorios) == 1


def test_relatorio_vazio_nao_quebra(ambiente):
    from src.report import weekly
    md = weekly.gerar_relatorio(dias=7, salvar=False)
    assert "Sem métricas no período" in md


def test_executar_semanal_completo(ambiente):
    db, vault = ambiente
    from src.report import weekly
    cid = db.salvar_conteudo(plataforma="facebook", legenda="x")
    pid = db.agendar_publicacao(cid, "facebook")
    db.marcar_publicado(pid, "EXT2")

    resumo = weekly.executar_semanal(FakeCollector(), dias=7)
    assert resumo["posts_medidos"] == 1
    assert "Relatório Semanal" in resumo["relatorio"]
