# -*- coding: utf-8 -*-
import sys, os
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (RAIZ, os.path.join(RAIZ, "src")):
    if p not in sys.path: sys.path.insert(0, p)
from image.arte_kit import montar_kit
from image.arte_informativo import frasco_demo
from agents.textos_informativo import gerar_textos_kit
from compliance import revisar

def test_kit_3():
    art = montar_kit([frasco_demo(),frasco_demo(),frasco_demo()],
        nome="Kit Capilar", itens=["Coco","Rícino","Alecrim"],
        tagline3=["Nutre","Fortalece","Brilho"], descricao="Três óleos 100% puros.")
    assert art.size == (1080,1350)

def test_kit_minimo():
    try:
        montar_kit([frasco_demo()], nome="x", itens=["a"], tagline3=["a","b","c"], descricao="y")
        assert False
    except ValueError:
        assert True

def test_textos_kit_compliant():
    r = gerar_textos_kit("Kit Bem-Estar", ["Sucupira","Andiroba","Copaíba"])  # todos sensiveis
    for t in r["tagline3"] + [r["descricao"]]:
        assert revisar(t).ok

if __name__ == "__main__":
    test_kit_3(); test_kit_minimo(); test_textos_kit_compliant()
    print("test_layout_kit OK")
