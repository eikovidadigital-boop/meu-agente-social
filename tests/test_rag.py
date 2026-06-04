"""
Testes do M1 — RAG.
Valida indexação, busca semântica e o comportamento incremental.
Usa um vault temporário com notas de exemplo — não depende de APIs externas.
"""
import shutil
import tempfile
from pathlib import Path

import pytest

from src import config


@pytest.fixture
def vault_temp(monkeypatch):
    """Cria um vault temporário e isola os dados do ChromaDB."""
    # Usa embedding offline (sem download de modelo) nos testes
    monkeypatch.setenv("RAG_EMBEDDING", "simple")
    tmp = Path(tempfile.mkdtemp())
    vault = tmp / "vault"
    vault.mkdir()
    chroma = tmp / "chroma"
    chroma.mkdir()

    # Isola config para não tocar nos dados reais
    monkeypatch.setattr(config, "VAULT_DIR", vault)
    monkeypatch.setattr(config, "CHROMA_DIR", chroma)

    # Notas de exemplo
    (vault / "alecrim.md").write_text(
        "O óleo de alecrim estimula o crescimento capilar e fortalece os fios. "
        "Ótimo para o couro cabeludo e contra a queda de cabelo.", encoding="utf-8")
    (vault / "rosa-mosqueta.md").write_text(
        "O óleo de rosa mosqueta regenera a pele, reduz cicatrizes e manchas. "
        "Tem ação anti-idade e hidrata profundamente.", encoding="utf-8")

    yield vault
    shutil.rmtree(tmp, ignore_errors=True)


def test_indexacao_inicial(vault_temp):
    from src.rag import indexer
    resumo = indexer.indexar_vault()
    assert resumo["processadas"] == 2
    assert resumo["puladas"] == 0


def test_busca_semantica_relevante(vault_temp):
    from src.rag import indexer, search
    indexer.indexar_vault()
    # Pergunta sobre cabelo deve trazer o alecrim primeiro
    resultados = search.buscar("o que ajuda no crescimento do cabelo?", top_k=2)
    assert len(resultados) > 0
    assert "alecrim" in resultados[0]["nota"]


def test_incremental_pula_inalteradas(vault_temp):
    from src.rag import indexer
    indexer.indexar_vault()
    # Segunda indexação sem mudanças: tudo pulado, nada processado
    resumo = indexer.indexar_vault()
    assert resumo["processadas"] == 0
    assert resumo["puladas"] == 2


def test_incremental_detecta_mudanca(vault_temp):
    from src.rag import indexer
    indexer.indexar_vault()
    # Altera uma nota
    (vault_temp / "alecrim.md").write_text("Conteúdo totalmente novo sobre alecrim.", encoding="utf-8")
    resumo = indexer.indexar_vault()
    assert resumo["processadas"] == 1
    assert resumo["puladas"] == 1


def test_contexto_nao_vazio(vault_temp):
    from src.rag import indexer, search
    indexer.indexar_vault()
    contexto = search.montar_contexto("cuidados com a pele", top_k=2)
    assert len(contexto) > 0
    assert "[" in contexto  # inclui o nome da nota
