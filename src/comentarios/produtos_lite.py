# -*- coding: utf-8 -*-
"""
Carrega o catálogo da EikoVida direto do Shopify (products.json),
de forma independente do resto do sistema. Usado só pelo atendimento.
"""
import re
import httpx

LOJA = "https://eikovida.com"


def _limpar_html(html: str) -> str:
    """Tira tags HTML e deixa um texto curto e limpo da descrição."""
    if not html:
        return ""
    texto = re.sub(r"<[^>]+>", " ", html)
    texto = re.sub(r"\s+", " ", texto).strip()
    return texto


def carregar_produtos(limite_paginas: int = 10):
    """
    Lê todos os produtos publicados da loja (com paginação).
    Retorna lista de dicts: {titulo, link, descricao, preco}
    """
    produtos = []
    pagina = 1
    while pagina <= limite_paginas:
        url = f"{LOJA}/products.json?limit=250&page={pagina}"
        try:
            r = httpx.get(url, timeout=30)
            r.raise_for_status()
            dados = r.json().get("products", [])
        except Exception as e:
            print(f"[produtos] erro ao ler página {pagina}: {e}")
            break

        if not dados:
            break

        for p in dados:
            handle = p.get("handle", "")
            variants = p.get("variants", [])
            preco = variants[0].get("price") if variants else None
            produtos.append({
                "titulo": p.get("title", "").strip(),
                "link": f"{LOJA}/products/{handle}",
                "descricao": _limpar_html(p.get("body_html", ""))[:400],
                "preco": preco,
            })
        pagina += 1

    print(f"[produtos] {len(produtos)} produtos carregados.")
    return produtos


def montar_contexto(produtos) -> str:
    """Monta um resumo enxuto do catálogo para a IA escolher o produto certo."""
    linhas = []
    for p in produtos:
        preco = f" | R${p['preco']}" if p.get("preco") else ""
        linhas.append(f"- {p['titulo']}{preco}\n  link: {p['link']}\n  descrição: {p['descricao']}")
    return "\n".join(linhas)
