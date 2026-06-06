"""
Catálogo de produtos reais.
Lê um arquivo simples (um produto por linha) com nome, URL da imagem real
(do Shopify) e uma info curta. O sistema usa a imagem REAL no post —
nada de imagem gerada por IA, pra o produto sair sempre correto.

Formato de cada linha:  NOME | URL_DA_IMAGEM | INFO
Linhas em branco ou começando com # são ignoradas.
"""
import re
from datetime import datetime
from pathlib import Path

import requests

from src import config


def carregar_do_shopify(loja_url: str = None, limite: int = 250, max_paginas: int = 20) -> list[dict]:
    """
    Lê TODOS os produtos AO VIVO do Shopify (loja.com/products.json), com paginação.
    Sempre que você cadastra um produto novo na loja, ele entra automaticamente
    no próximo post — sem nenhum trabalho manual.
    """
    loja_url = loja_url or config.SHOPIFY_LOJA
    if not loja_url:
        return []
    base = loja_url.rstrip("/")
    produtos = []
    for pagina in range(1, max_paginas + 1):
        url = f"{base}/products.json?limit={limite}&page={pagina}"
        r = requests.get(url, timeout=30)
        r.raise_for_status()
        lote = r.json().get("products", [])
        if not lote:
            break
        for p in lote:
            imgs = p.get("images") or []
            if not imgs:
                continue
            descricao = re.sub(r"<[^>]+>", " ", p.get("body_html") or "")
            descricao = re.sub(r"\s+", " ", descricao).strip()
            produtos.append({
                "nome": p.get("title", "").strip(),
                "imagem": imgs[0].get("src", ""),
                "info": descricao[:200],
            })
        if len(lote) < limite:   # última página
            break
    return [p for p in produtos if p["imagem"]]


def carregar(caminho=None) -> list[dict]:
    caminho = Path(caminho or config.CATALOGO_PATH)
    produtos = []
    if not caminho.exists():
        return produtos
    for linha in caminho.read_text(encoding="utf-8").splitlines():
        linha = linha.strip()
        if not linha or linha.startswith("#"):
            continue
        partes = [p.strip() for p in linha.split("|")]
        if len(partes) >= 2 and partes[1]:
            produtos.append({
                "nome": partes[0],
                "imagem": partes[1],
                "info": partes[2] if len(partes) > 2 else "",
            })
    return produtos


def escolher(produtos: list[dict], indice: int = None) -> dict | None:
    """Escolhe um produto. Por padrão, rotaciona pelo dia do ano (varia a cada dia)."""
    if not produtos:
        return None
    if indice is None:
        indice = datetime.now().timetuple().tm_yday
    return produtos[indice % len(produtos)]
