# -*- coding: utf-8 -*-
import sys, os
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (RAIZ, os.path.join(RAIZ, "src")):
    if p not in sys.path: sys.path.insert(0, p)
from PIL import Image, ImageDraw
from image.foto import score_recorte, melhor_recorte, urls_produto

def _frasco_compacto():            # preenche bem o bbox -> score baixo
    im = Image.new("RGBA", (300, 600), (0,0,0,0))
    ImageDraw.Draw(im).rectangle([40, 20, 260, 580], fill=(150,90,40,255))
    return im

def _com_splash():                 # produto + respingos espalhados -> bbox enorme, score alto
    im = Image.new("RGBA", (600, 600), (0,0,0,0))
    d = ImageDraw.Draw(im)
    d.rectangle([260, 200, 340, 560], fill=(150,90,40,255))   # frasco fino
    for xy in [(20,20),(560,40),(40,560),(570,520),(300,30)]: # respingos nos cantos
        d.ellipse([xy[0]-15, xy[1]-15, xy[0]+15, xy[1]+15], fill=(120,200,40,255))
    return im

def test_score_ordena():
    assert score_recorte(_frasco_compacto()) < score_recorte(_com_splash())

def test_escolhe_a_limpa():
    fotos = {"limpa": _frasco_compacto(), "splash": _com_splash()}
    class CompFake:
        def recortar_produto(self, dados, usar_ia=False): return fotos[dados]
        def bbox_conteudo(self, rgba):
            b = rgba.split()[-1].getbbox(); return rgba.crop(b) if b else rgba
    produto = {"images": [{"src": "splash"}, {"src": "limpa"}]}
    rgba, sc = melhor_recorte(produto, lambda u: u, CompFake())
    # a escolhida deve ter score baixo (a limpa)
    assert sc < 0.3, sc

if __name__ == "__main__":
    test_score_ordena(); test_escolhe_a_limpa(); print("test_foto OK")
