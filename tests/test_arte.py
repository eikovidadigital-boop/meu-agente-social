"""Testes da arte do post (montagem) e do agente de textos."""
import io

from PIL import Image, ImageDraw

from src.agents import arte_textos
from src.image import arte


def _produto_fake() -> bytes:
    img = Image.new("RGB", (400, 500), "white")
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([150, 120, 250, 380], radius=20, fill=(90, 60, 40))
    buf = io.BytesIO(); img.save(buf, "PNG")
    return buf.getvalue()


TEXTOS = {
    "titulo": "ÓLEO DE TESTE",
    "subtitulo": "BENEFÍCIO DE TESTE",
    "beneficio": ["RICO EM", "VITAMINA", "NATURAL"],
    "tagline": ["100% NATURAL", "PRENSADO A FRIO"],
}


def test_arte_monta_jpeg_4x5():
    jpeg = arte.montar(_produto_fake(), TEXTOS, fundo_img=None, seed=1, usar_ia_recorte=False)
    out = Image.open(io.BytesIO(jpeg))
    assert out.size == (1080, 1350)   # formato 4:5
    assert out.format == "JPEG"


def test_arte_usa_fundo_da_ia():
    fundo = Image.new("RGB", (1024, 1024), (30, 60, 30))
    jpeg = arte.montar(_produto_fake(), TEXTOS, fundo_img=fundo, seed=0, usar_ia_recorte=False)
    assert Image.open(io.BytesIO(jpeg)).size == (1080, 1350)


def test_arte_textos_fallback_completo():
    d = arte_textos._fallback("Óleo de Pequi", arte_textos.FOCOS[0])
    for k in ("titulo", "subtitulo", "beneficio", "tagline", "foco"):
        assert k in d
    assert len(d["beneficio"]) == 3 and len(d["tagline"]) == 2


def test_arte_textos_foco_alterna():
    # o mesmo produto (mesma posição) recebe focos diferentes a cada volta
    f1 = arte_textos.escolher_foco(5, 8)
    f2 = arte_textos.escolher_foco(13, 8)
    f3 = arte_textos.escolher_foco(21, 8)
    assert f1["id"] != f2["id"] != f3["id"]
    assert {f1["id"], f2["id"], f3["id"]} == {"PELE", "CABELO", "SAUDE"}


def test_arte_textos_parse_json():
    # injeta um LLM falso que devolve JSON válido (não gasta API)
    class FakeLLM:
        def gerar(self, prompt, system="", max_tokens=400):
            return ('{"titulo":"ÓLEO X","subtitulo":"SUB","beneficio":["A","B","C"],'
                    '"tagline":["L1","L2"]}')
    d = arte_textos.gerar_textos("Óleo X", "info", foco=arte_textos.FOCOS[2], llm=FakeLLM())
    assert d["titulo"] == "ÓLEO X"
    assert len(d["beneficio"]) == 3
    assert d["foco"] == "SAUDE"
