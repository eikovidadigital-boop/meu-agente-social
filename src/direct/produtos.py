# -*- coding: utf-8 -*-
"""
Produtos para o agente de Direct.

- Carrega o catalogo real da loja (eikovida.com/products.json, com paginacao).
- Monta um "cardapio" curto (nome + descricao curta) pra IA usar SO o que e real.
- Acha o produto que o cliente mencionou e devolve o LINK direto + preco.

Nunca inventa: se nao casar com nenhum produto, devolve None e o agente cai
no caminho de catalogo (e-mail + WhatsApp).
"""
import re
import unicodedata

from src import util_net as net

LOJA = "https://eikovida.com"
PRODUCTS_JSON = LOJA + "/products.json"


def _norm(s):
    s = unicodedata.normalize("NFKD", (s or "")).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9 ]", " ", s.lower()).strip()


def _limpa_html(html):
    txt = re.sub(r"<[^>]+>", " ", html or "")
    txt = re.sub(r"\s+", " ", txt).strip()
    return txt


def carregar_produtos():
    """Baixa todos os produtos da loja (pagina de 250 em 250)."""
    produtos = []
    pagina = 1
    while True:
        url = f"{PRODUCTS_JSON}?limit=250&page={pagina}"
        try:
            data = net.get(url, timeout=40).json()
        except Exception:
            break
        lote = (data or {}).get("products", [])
        if not lote:
            break
        produtos.extend(lote)
        if len(lote) < 250:
            break
        pagina += 1
    return produtos


def link_produto(p):
    return f"{LOJA}/products/{p.get('handle','')}"


def preco_produto(p):
    for v in p.get("variants", []) or []:
        preco = v.get("price")
        if preco:
            try:
                return f"R$ {float(preco):.2f}".replace(".", ",")
            except Exception:
                return f"R$ {preco}"
    return ""


def cardapio(produtos, max_itens=60):
    """Lista curta (nome | descricao curta) pra IA usar so o que e real."""
    linhas = []
    for p in produtos[:max_itens]:
        nome = p.get("title", "")
        desc = _limpa_html(p.get("body_html", ""))[:140]
        linhas.append(f"- {nome}" + (f" :: {desc}" if desc else ""))
    return "\n".join(linhas)


def achar_produto(texto_cliente, produtos):
    """Acha o produto mais provavel mencionado pelo cliente (por palavra do nome).
    Devolve o produto ou None."""
    alvo = _norm(texto_cliente)
    if not alvo:
        return None
    melhor, melhor_score = None, 0
    for p in produtos:
        nome = _norm(p.get("title", ""))
        # palavras significativas do nome do produto (ignora 'oleo','de','ml'...)
        palavras = [w for w in nome.split()
                    if len(w) >= 4 and w not in ("oleo", "natural", "vegetal", "puro")]
        score = sum(1 for w in palavras if w in alvo)
        if score > melhor_score:
            melhor, melhor_score = p, score
    return melhor if melhor_score > 0 else None


def site_no_ar():
    """Checa se a loja esta no ar agora (pra responder duvidas sobre o site)."""
    try:
        r = net.get(LOJA, timeout=15)
        cod = getattr(r, "status_code", 200)
        return 200 <= int(cod) < 400
    except Exception:
        return False
