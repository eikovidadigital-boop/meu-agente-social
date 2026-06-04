"""
Testes do M3 — Geração de Imagens.
Usam funções falsas injetadas: não chamam OpenAI/ImgBB de verdade.
Verificam a orquestração, o caminho img2img vs texto e propagação de erro.
"""
import pytest

from src.image.generator import ImageGenerator


def test_criar_orquestra_gerar_e_hospedar():
    chamadas = {"gerar": 0, "hospedar": 0}

    def fake_gerar(prompt, produto_img_url=None):
        chamadas["gerar"] += 1
        return "BASE64FALSO"

    def fake_hospedar(b64):
        chamadas["hospedar"] += 1
        assert b64 == "BASE64FALSO"
        return "https://i.ibb.co/teste.png"

    gen = ImageGenerator(gerar_fn=fake_gerar, hospedar_fn=fake_hospedar)
    url = gen.criar("um óleo bonito")
    assert url == "https://i.ibb.co/teste.png"
    assert chamadas == {"gerar": 1, "hospedar": 1}


def test_img2img_recebe_url_do_produto():
    recebido = {}

    def fake_gerar(prompt, produto_img_url=None):
        recebido["url"] = produto_img_url
        return "B64"

    gen = ImageGenerator(gerar_fn=fake_gerar, hospedar_fn=lambda b64: "u")
    gen.criar("prompt", produto_img_url="https://eikovida.com/produto.png")
    assert recebido["url"] == "https://eikovida.com/produto.png"


def test_text2img_sem_produto():
    recebido = {}

    def fake_gerar(prompt, produto_img_url=None):
        recebido["url"] = produto_img_url
        return "B64"

    gen = ImageGenerator(gerar_fn=fake_gerar, hospedar_fn=lambda b64: "u")
    gen.criar("prompt")
    assert recebido["url"] is None


def test_erro_na_geracao_propaga():
    def fake_gerar(prompt, produto_img_url=None):
        raise RuntimeError("falha na API")

    gen = ImageGenerator(gerar_fn=fake_gerar, hospedar_fn=lambda b64: "u")
    with pytest.raises(RuntimeError, match="falha na API"):
        gen.criar("prompt")
