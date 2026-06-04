"""
Testes do M5 — Publicação.
Usam HTTP falso injetado: não chamam a Graph API.
Cobrem Instagram, Facebook e o orquestrador (sucesso e erro).
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


def test_instagram_fluxo_completo():
    from src.social.instagram import InstagramPublisher
    chamadas = []

    def fake_post(url, params):
        chamadas.append(url)
        if url.endswith("/media"):
            return {"id": "CONTAINER1"}
        if url.endswith("/media_publish"):
            return {"id": "MEDIA1"}
        if url.endswith("/comments"):
            return {"id": "COMMENT1"}
        return {}

    ig = InstagramPublisher(account_id="IG", token="T", post_fn=fake_post, sleep_fn=lambda s: None)
    media_id = ig.publicar("http://img", "legenda", "#a #b")
    assert media_id == "MEDIA1"
    # criou container, publicou e comentou hashtags
    assert any(u.endswith("/media") for u in chamadas)
    assert any(u.endswith("/media_publish") for u in chamadas)
    assert any(u.endswith("/comments") for u in chamadas)


def test_instagram_erro_no_container():
    from src.social.instagram import InstagramPublisher

    def fake_post(url, params):
        return {"error": {"message": "token inválido"}}

    ig = InstagramPublisher(account_id="IG", token="T", post_fn=fake_post, sleep_fn=lambda s: None)
    with pytest.raises(RuntimeError, match="token inválido"):
        ig.publicar("http://img", "legenda")


def test_facebook_posta_com_hashtags():
    from src.social.facebook import FacebookPublisher
    recebido = {}

    def fake_post(url, params):
        recebido["params"] = params
        return {"id": "FBPOST1"}

    fb = FacebookPublisher(page_id="PG", token="T", post_fn=fake_post)
    post_id = fb.publicar("http://img", "legenda", "#x #y")
    assert post_id == "FBPOST1"
    # legenda e hashtags vão juntas no texto do Facebook
    assert "legenda" in recebido["params"]["message"]
    assert "#x" in recebido["params"]["message"]


def test_publisher_marca_publicado(db_temp):
    from src.social.publisher import Publisher

    class FakeAdapter:
        plataforma = "instagram"
        def publicar(self, image_url, legenda, hashtags=""):
            return "EXT999"

    cid = db_temp.salvar_conteudo(plataforma="instagram", legenda="oi", imagem_url="http://i")
    db_temp.agendar_publicacao(cid, "instagram")

    pub = Publisher([FakeAdapter()], sleep_fn=lambda s: None)
    resultados = pub.publicar_pendentes()
    assert resultados[0]["status"] == "ok"
    assert resultados[0]["post_id"] == "EXT999"
    # saiu das pendentes
    assert db_temp.publicacoes_pendentes() == []


def test_publisher_marca_erro(db_temp):
    from src.social.publisher import Publisher

    class FakeAdapterFalha:
        plataforma = "facebook"
        def publicar(self, image_url, legenda, hashtags=""):
            raise RuntimeError("API caiu")

    cid = db_temp.salvar_conteudo(plataforma="facebook", legenda="oi", imagem_url="http://i")
    db_temp.agendar_publicacao(cid, "facebook")

    pub = Publisher([FakeAdapterFalha()], sleep_fn=lambda s: None)
    resultados = pub.publicar_pendentes()
    assert resultados[0]["status"] == "erro"
    assert "API caiu" in resultados[0]["motivo"]
    # não ficou pendente
    assert db_temp.publicacoes_pendentes() == []
