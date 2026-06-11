# -*- coding: utf-8 -*-
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from src.carrossel_conteudo import gerar_itens, FALLBACK
from src.compliance import revisar
from src import rotacao

def test_itens_reserva():
    for tipo in ("beneficios", "modo_usar", "curiosidades"):
        itens = gerar_itens("Coco", tipo, None)
        assert len(itens) == 3, f"{tipo}: esperado 3 itens"
        for tit, tx in itens:
            assert revisar(tit).ok and revisar(tx).ok, f"{tipo}: texto reprovado no compliance"
    print("OK itens (reserva) compliant nos 3 tipos")

def test_rotacao_tipos():
    vistos = {rotacao.tipo_carrossel(i) for i in range(6)}
    assert vistos == {"beneficios", "curiosidades", "modo_usar"}, vistos
    print("OK rotacao intercala os 3 tipos")

if __name__ == "__main__":
    test_itens_reserva(); test_rotacao_tipos(); print("test_carrossel OK")
