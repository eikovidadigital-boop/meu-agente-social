"""Testes do recorte do produto e dos cenários."""
import io

from PIL import Image, ImageDraw

from src.image import composer


def _produto_fake() -> bytes:
    img = Image.new("RGB", (400, 500), "white")
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([150, 120, 250, 380], radius=20, fill=(90, 60, 40))
    d.rounded_rectangle([160, 200, 240, 300], radius=8, fill=(135, 173, 37))
    buf = io.BytesIO(); img.save(buf, "PNG")
    return buf.getvalue()


def test_recorte_deixa_transparente_e_opaco():
    rec = composer.recortar_produto(_produto_fake(), usar_ia=False)
    assert rec.mode == "RGBA"
    minimo, maximo = rec.split()[-1].getextrema()
    assert minimo == 0      # fundo removido
    assert maximo == 255    # produto preservado


def test_bbox_corta_transparencia():
    rec = composer.recortar_produto(_produto_fake(), usar_ia=False)
    cortado = composer.bbox_conteudo(rec)
    assert cortado.width <= rec.width and cortado.height <= rec.height


def test_ha_cenarios_e_rotacionam():
    assert len(composer.CENARIOS) >= 4
    assert composer.escolher_cenario(0) != composer.escolher_cenario(1)
