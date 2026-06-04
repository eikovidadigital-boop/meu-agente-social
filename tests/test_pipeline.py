"""
Testes do M6 — Pipeline diário.
Injeta dependências falsas (LLM, gerador de imagem, publicador) e usa
vault + banco temporários. Verifica a orquestração ponta a ponta sem APIs.
"""
import shutil
import tempfile
from pathlib import Path

import pytest

from src import config


class FakeLLM:
    def __init__(self, resposta="texto gerado"):
        self.resposta = resposta

    def gerar(self, prompt, system="", max_tokens=900):
        return self.resposta


class FakeImageGen:
    def __init__(self):
        self.chamou = 0

    def criar(self, prompt, produto_img_url=None):
        self.chamou += 1
        return "https://i.ibb.co/fake.png"


class FakePublisher:
    def __init__(self):
        self.chamou = 0

    def publicar_pendentes(self):
        self.chamou += 1
        return [{"id": 1, "status": "ok", "post_id": "EXT1"}]


@pytest.fixture
def ambiente(monkeypatch):
    monkeypatch.setenv("RAG_EMBEDDING", "simple")
    tmp = Path(tempfile.mkdtemp())
    vault = tmp / "vault"; vault.mkdir()
    chroma = tmp / "chroma"; chroma.mkdir()
    monkeypatch.setattr(config, "VAULT_DIR", vault)
    monkeypatch.setattr(config, "CHROMA_DIR", chroma)
    monkeypatch.setattr(config, "DB_PATH", tmp / "teste.db")
    (vault / "marca.md").write_text(
        "EikoVida, óleos naturais, tom acolhedor, foco em cabelo e pele.", encoding="utf-8")
    yield
    shutil.rmtree(tmp, ignore_errors=True)


def test_pipeline_gera_e_publica(ambiente):
    from src.pipeline import executar_diario
    from src.storage import db

    img = FakeImageGen()
    pub = FakePublisher()
    resumo = executar_diario(
        objetivo="óleo de alecrim para cabelo",
        plataformas=("instagram", "facebook"),
        llm=FakeLLM("conteúdo"),
        image_gen=img,
        publisher=pub,
    )

    # gerou imagem uma vez só e reaproveitou
    assert img.chamou == 1
    assert resumo["imagem_url"] == "https://i.ibb.co/fake.png"
    # criou conteúdo para as 2 plataformas
    assert len(resumo["conteudos"]) == 2
    # publicou
    assert pub.chamou == 1
    # conteúdos salvos no banco com a mesma imagem
    salvos = db.listar_conteudo()
    assert len(salvos) == 2
    assert all(c["imagem_url"] == "https://i.ibb.co/fake.png" for c in salvos)
    plataformas = {c["plataforma"] for c in salvos}
    assert plataformas == {"instagram", "facebook"}


def test_objetivo_do_dia_retorna_texto():
    from src.pipeline import objetivo_do_dia
    obj = objetivo_do_dia()
    assert isinstance(obj, str) and len(obj) > 0


def test_pipeline_uma_plataforma(ambiente):
    from src.pipeline import executar_diario
    resumo = executar_diario(
        objetivo="teste", plataformas=("instagram",),
        llm=FakeLLM(), image_gen=FakeImageGen(), publisher=FakePublisher(),
    )
    assert len(resumo["conteudos"]) == 1
