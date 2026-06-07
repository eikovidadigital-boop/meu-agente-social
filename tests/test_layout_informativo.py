# -*- coding: utf-8 -*-
import sys, os
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (RAIZ, os.path.join(RAIZ, "src")):
    if p not in sys.path: sys.path.insert(0, p)
from image.arte_informativo import montar, frasco_demo, escolher_layout, FOCO_LABEL

DADOS = dict(nome="Rosa Mosqueta", tagline3=["Regenera","Ilumina","Renova"],
             descricao="Óleo 100% puro para o cuidado da pele.",
             beneficios3=["Hidratação profunda","Maciez sem oleosidade","Rico em nutrientes"])

def test_tamanhos():
    for vol in ["120 ml", "30 ml"]:
        art = montar(frasco_demo(vol), foco="PELE", volume=vol, **DADOS)
        assert art.size == (1080, 1350)

def test_focos():
    for foco in ["PELE","CABELO","SAUDE"]:
        art = montar(frasco_demo(), foco=foco, **DADOS)
        assert art.size == (1080, 1350) and foco in FOCO_LABEL

def test_kit_recusado():
    try:
        montar(frasco_demo(), foco="PELE", eh_kit=True, **DADOS); assert False
    except ValueError:
        assert True

def test_roteamento():
    assert escolher_layout(False, 0) == "dramatico"
    assert escolher_layout(False, 1) == "informativo"
    assert escolher_layout(True, 1) == "kit"

if __name__ == "__main__":
    test_tamanhos(); test_focos(); test_kit_recusado(); test_roteamento()
    print("test_layout_informativo OK")
