"""
Testes do M2 — Agentes de IA.
Usam um LLM falso injetado: não chamam a API real, são determinísticos
e verificam construção de prompt, integração com RAG e parsing.
"""
import shutil
import tempfile
from pathlib import Path

import pytest

from src import config


class FakeLLM:
    """LLM falso: registra o prompt recebido e devolve resposta canned."""
    def __init__(self, resposta: str):
        self.resposta = resposta
        self.ultimo_prompt = None
        self.ultimo_system = None

    def gerar(self, prompt: str, system: str = "", max_tokens: int = 900) -> str:
        self.ultimo_prompt = prompt
        self.ultimo_system = system
        return self.resposta


@pytest.fixture
def vault_indexado(monkeypatch):
    monkeypatch.setenv("RAG_EMBEDDING", "simple")
    tmp = Path(tempfile.mkdtemp())
    vault = tmp / "vault"; vault.mkdir()
    chroma = tmp / "chroma"; chroma.mkdir()
    monkeypatch.setattr(config, "VAULT_DIR", vault)
    monkeypatch.setattr(config, "CHROMA_DIR", chroma)
    (vault / "marca.md").write_text(
        "A marca EikoVida usa óleos naturais. Cor verde 87ad25. "
        "Tom acolhedor e empoderado. Foco em cabelo e pele saudáveis.", encoding="utf-8")
    from src.rag import indexer
    indexer.indexar_vault()
    yield vault
    shutil.rmtree(tmp, ignore_errors=True)


def test_ideias_parse_linhas(vault_indexado):
    from src.agents import ideas
    fake = FakeLLM("Ideia A\nIdeia B\nIdeia C\nIdeia D")
    resultado = ideas.gerar_ideias("crescimento no Instagram", n=3, llm=fake)
    assert resultado == ["Ideia A", "Ideia B", "Ideia C"]


def test_ideias_usa_contexto_rag(vault_indexado):
    from src.agents import ideas
    fake = FakeLLM("X")
    ideas.gerar_ideias("óleo para cabelo", n=1, llm=fake)
    # o prompt deve conter o contexto recuperado do vault
    assert "EikoVida" in fake.ultimo_prompt


def test_legenda_instagram_vs_facebook(vault_indexado):
    from src.agents import captions
    fake = FakeLLM("legenda")
    captions.gerar_legenda("óleo de alecrim", "instagram", llm=fake)
    prompt_ig = fake.ultimo_prompt
    captions.gerar_legenda("óleo de alecrim", "facebook", llm=fake)
    prompt_fb = fake.ultimo_prompt
    # cada plataforma recebe instrução de estilo diferente
    assert "Instagram" in prompt_ig
    assert "Facebook" in prompt_fb
    assert prompt_ig != prompt_fb


def test_legenda_plataforma_invalida(vault_indexado):
    from src.agents import captions
    with pytest.raises(ValueError):
        captions.gerar_legenda("x", "linkedin", llm=FakeLLM("y"))


def test_hashtags_inclui_base_e_rotaciona(vault_indexado):
    from src.agents import hashtags
    fake = FakeLLM("#a #b #c #d #e #f #g #h #i #j #k #l #m #n #o #p")
    base = ["#eikovida", "#oleosnaturais"]
    resultado = hashtags.gerar_hashtags("óleo de alecrim", n=8, base=base, llm=fake)
    tags = resultado.split()
    # base sempre presente
    assert "#eikovida" in tags
    assert "#oleosnaturais" in tags
    # sem duplicatas
    assert len(tags) == len(set(t.lower() for t in tags))


def test_image_prompt_usa_contexto(vault_indexado):
    from src.agents import image_prompt
    fake = FakeLLM("a beautiful product photo")
    resultado = image_prompt.gerar_prompt_imagem("óleo de alecrim", llm=fake)
    assert resultado == "a beautiful product photo"
    assert "EikoVida" in fake.ultimo_prompt
