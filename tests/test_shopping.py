# -*- coding: utf-8 -*-
import sys, os
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (RAIZ, os.path.join(RAIZ, "src")):
    if p not in sys.path: sys.path.insert(0, p)
import social_shopping as sh

# Catalogo Meta simulado: MESMO oleo em 30ml e 120ml, mais kit e outro oleo
CATALOGO = [
    {"id": "META_LIMAO_30",  "name": "Óleo de Limão Extra Virgem 30ml",  "retailer_id": "shopify_BR_77_1030"},
    {"id": "META_LIMAO_120", "name": "Óleo de Limão Extra Virgem 120ml", "retailer_id": "shopify_BR_77_1120"},
    {"id": "META_COCO_120",  "name": "Óleo de Coco Extra Virgem 120ml",  "retailer_id": "shopify_BR_88_2120"},
    {"id": "META_KIT",       "name": "Kit 3 Óleos Capilares",            "retailer_id": "shopify_BR_99_3000"},
]

# Produtos do dia, como vêm do products.json (com variantes/ids da Shopify)
LIMAO_30  = {"title": "Óleo de Limão Extra Virgem 30ml Eiko",  "variants": [{"id": 1030}]}
LIMAO_120 = {"title": "Óleo de Limão Extra Virgem 120ml Eiko", "variants": [{"id": 1120}]}
KIT       = {"title": "Kit 3 Óleos Capilares Eiko",            "variants": [{"id": 3000}]}
NOVO      = {"title": "Óleo de Abacate 60ml Eiko",             "variants": [{"id": 9999}]}  # nao esta no catalogo

def _t(prod): return prod["title"]

def test_por_retailer_id_distingue_tamanho():
    sh._cache = CATALOGO
    assert sh.product_id_para(_t(LIMAO_30),  sh.ids_shopify(LIMAO_30))  == "META_LIMAO_30"
    assert sh.product_id_para(_t(LIMAO_120), sh.ids_shopify(LIMAO_120)) == "META_LIMAO_120"
    assert sh.product_id_para(_t(KIT),       sh.ids_shopify(KIT))       == "META_KIT"

def test_por_nome_distingue_tamanho():
    sh._cache = CATALOGO
    # sem retailer: cai no nome, e o volume tem que separar 30 de 120
    assert sh.product_id_para(_t(LIMAO_30))  == "META_LIMAO_30"
    assert sh.product_id_para(_t(LIMAO_120)) == "META_LIMAO_120"

def test_nao_marca_produto_inexistente():
    sh._cache = CATALOGO
    assert sh.product_id_para(_t(NOVO), sh.ids_shopify(NOVO)) is None

if __name__ == "__main__":
    sh._cache = CATALOGO
    print("CASAMENTO POR CÓDIGO DA SHOPIFY (retailer_id):")
    for p in (LIMAO_30, LIMAO_120, KIT):
        print(f"  {_t(p):42} -> {sh.product_id_para(_t(p), sh.ids_shopify(p))}")
    print("\nCASAMENTO SÓ POR NOME (sem código):")
    for p in (LIMAO_30, LIMAO_120):
        print(f"  {_t(p):42} -> {sh.product_id_para(_t(p))}")
    print("\nPRODUTO QUE NÃO ESTÁ NO CATÁLOGO:")
    print(f"  {_t(NOVO):42} -> {sh.product_id_para(_t(NOVO), sh.ids_shopify(NOVO))}  (não marca nada)")
    test_por_retailer_id_distingue_tamanho()
    test_por_nome_distingue_tamanho()
    test_nao_marca_produto_inexistente()
    print("\n>>> TODOS OS TESTES PASSARAM")
