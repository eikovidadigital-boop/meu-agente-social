"""Testes da escolha automática da melhor foto do produto."""
import io

from PIL import Image, ImageDraw

from src import catalogo
from src.image import composer


def _img_bytes(splash_branco: bool) -> bytes:
    img = Image.new("RGB", (400, 500), "white")
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([150, 120, 250, 380], radius=20, fill=(90, 60, 40))
    if splash_branco:
        # mancha clara/acinzentada espalhada (simula splash branco difícil)
        d.ellipse([40, 60, 360, 300], fill=(238, 238, 235))
        d.rounded_rectangle([150, 120, 250, 380], radius=20, fill=(90, 60, 40))
    buf = io.BytesIO(); img.save(buf, "PNG")
    return buf.getvalue()


def test_score_penaliza_splash_branco():
    s_limpa = composer.score_recorte(_img_bytes(False))
    s_splash = composer.score_recorte(_img_bytes(True))
    assert s_splash > s_limpa


def test_melhor_imagem_escolhe_a_limpa():
    limpa = _img_bytes(False)
    splash = _img_bytes(True)
    store = {"u_limpa": limpa, "u_splash": splash}
    produto = {"nome": "X", "imagem": "u_splash",
               "imagens": ["u_splash", "u_limpa"], "info": ""}
    escolhida = catalogo.melhor_imagem(produto, lambda u: store[u])
    assert escolhida == limpa


def test_melhor_imagem_uma_so():
    produto = {"nome": "X", "imagem": "u", "imagens": ["u"], "info": ""}
    assert catalogo.melhor_imagem(produto, lambda u: b"abc") == b"abc"
