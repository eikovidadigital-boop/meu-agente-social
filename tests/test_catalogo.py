"""Testes da escolha automática da melhor foto do produto."""
import io

from PIL import Image, ImageDraw

from src import catalogo
from src.image import composer


def _img_compacta() -> bytes:
    """Produto compacto e centralizado (foto limpa) -> preenche bem o quadro."""
    img = Image.new("RGB", (400, 500), "white")
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([150, 110, 250, 390], radius=20, fill=(90, 60, 40))
    buf = io.BytesIO(); img.save(buf, "PNG")
    return buf.getvalue()


def _img_espalhada() -> bytes:
    """Produto + splash/respingos espalhados (foto com splash) -> preenche pouco."""
    img = Image.new("RGB", (400, 500), "white")
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([170, 200, 230, 360], radius=16, fill=(90, 60, 40))
    # tiras finas de "splash" espalhadas até os cantos -> bbox grande, esparso
    d.line([(40, 60), (360, 120)], fill=(60, 150, 40), width=8)
    d.line([(60, 440), (350, 400)], fill=(60, 150, 40), width=8)
    d.ellipse([40, 60, 90, 110], fill=(40, 30, 80))
    d.ellipse([330, 410, 370, 450], fill=(40, 30, 80))
    buf = io.BytesIO(); img.save(buf, "PNG")
    return buf.getvalue()


def test_score_penaliza_foto_espalhada():
    s_limpa = composer.score_recorte(_img_compacta())
    s_splash = composer.score_recorte(_img_espalhada())
    assert s_splash > s_limpa


def test_melhor_imagem_escolhe_a_limpa():
    limpa = _img_compacta()
    splash = _img_espalhada()
    store = {"u_limpa": limpa, "u_splash": splash}
    produto = {"nome": "X", "imagem": "u_splash",
               "imagens": ["u_splash", "u_limpa"], "info": ""}
    escolhida = catalogo.melhor_imagem(produto, lambda u: store[u])
    assert escolhida == limpa


def test_melhor_imagem_uma_so():
    produto = {"nome": "X", "imagem": "u", "imagens": ["u"], "info": ""}
    assert catalogo.melhor_imagem(produto, lambda u: b"abc") == b"abc"
