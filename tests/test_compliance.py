# -*- coding: utf-8 -*-
import sys, os
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (RAIZ, os.path.join(RAIZ, "src")):
    if p not in sys.path: sys.path.insert(0, p)
from compliance import revisar, suavizar, eh_sensivel, focos_permitidos

RUINS = [
    "Óleo que cura a queda e trata a calvície",
    "Você sofre de ansiedade? É o remédio natural",
    "Resultado garantido, clinicamente comprovado",
    "Antioxidante que protege as células e previne doenças",
    "Reverte o envelhecimento e acaba com a celulite",
]
# claims tipicos ANVISA dos 3 sensiveis -> TODOS devem ser barrados
ANVISA = [
    "Óleo de copaíba anti-inflamatório e cicatrizante natural",
    "Copaíba com ação antisséptica para feridas",
    "Sucupira alivia a dor das articulações e combate a artrite",
    "Sucupira indicada para reumatismo e ácido úrico",
    "Andiroba repelente natural contra mosquitos",
    "Andiroba anti-inflamatória para dores musculares",
]
BONS = [
    "Óleo 100% puro, usado no cuidado dos fios",
    "Rico em ômega 3, 6 e 9. Ideal para temperar saladas",
    "Hidratação profunda que deixa a pele macia",
    "Faz parte do seu ritual de cuidado com a pele",
    "Óleo de copaíba 100% puro para hidratar e dar maciez à pele",
]

def test_barra_ruins():
    for t in RUINS: assert not revisar(t).ok, t

def test_barra_anvisa():
    for t in ANVISA: assert not revisar(t).ok, t

def test_libera_bons():
    for t in BONS: assert revisar(t).ok, t

def test_sensiveis():
    assert eh_sensivel("Óleo de Copaíba") and eh_sensivel("Sucupira") and eh_sensivel("ANDIROBA")
    assert not eh_sensivel("Rosa Mosqueta")
    # sensiveis nunca podem usar foco SAUDE
    assert "SAUDE" not in focos_permitidos("Copaíba")
    assert "SAUDE" in focos_permitidos("Linhaça")

def test_suaviza():
    assert revisar(suavizar("remove as manchas")).ok

if __name__ == "__main__":
    test_barra_ruins(); test_barra_anvisa(); test_libera_bons(); test_sensiveis(); test_suaviza()
    print("test_compliance OK")
