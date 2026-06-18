# -*- coding: utf-8 -*-
"""
TESTE ISOLADO da publicacao no Facebook.

Roda manualmente pelo GitHub Actions (botao "Run workflow") para confirmar,
ANTES de ligar no fluxo automatico, que:
  - o PAGE_ACCESS_TOKEN tem a permissao pages_manage_posts;
  - a Pagina do Facebook publica certo.

Ele pega a imagem do PRIMEIRO produto da loja (eikovida.com/products.json),
publica uma foto unica de teste e mostra o resultado. Pode apagar o post depois.
"""

import httpx
from src.facebook.publicador import publicar_no_facebook

LEGENDA_TESTE = "Teste de integracao EikoVida no Facebook. (post de teste - pode apagar)"


def _imagem_de_teste():
    """Pega a imagem do primeiro produto da loja (sempre publica e existente)."""
    r = httpx.get("https://eikovida.com/products.json?limit=1", timeout=30.0)
    produtos = r.json().get("products", [])
    if not produtos or not produtos[0].get("images"):
        raise RuntimeError("Nao achei imagem de produto na loja para o teste.")
    return produtos[0]["images"][0]["src"]


if __name__ == "__main__":
    try:
        url = _imagem_de_teste()
        print(f"[teste] Usando imagem: {url}")
        post_id = publicar_no_facebook(url, LEGENDA_TESTE)
        print(f"OK! Post de teste publicado no Facebook: {post_id}")
    except Exception as e:
        print(f"ERRO no teste do Facebook: {e}")
        raise
