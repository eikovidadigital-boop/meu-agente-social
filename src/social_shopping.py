# -*- coding: utf-8 -*-
"""
Instagram Shopping: casa o produto do dia com o item EXATO do catalogo Meta
(distingue 30ml, 120ml e kit) e devolve as etiquetas (product_tags).

Casamento, em ordem de prioridade:
1) retailer_id  -> id/variante/SKU da Shopify (exato; nunca confunde tamanho).
2) nome completo COM o volume (limão 120ml != limão 30ml).
Produto novo na loja aparece sozinho: o catalogo e o products.json sao lidos ao vivo.
"""
import os
import re
import unicodedata
import requests

try:
    from src import config
except Exception:
    config = None

API = "https://graph.facebook.com/v25.0"

_STOP = {"oleo", "oleos", "de", "da", "do", "e", "eiko", "eikovida", "extra",
         "virgem", "vegetal", "natural", "puro", "pura", "prensado", "prensada",
         "frio", "nao", "refinado", "refinada", "ml"}


def _cfg(nome, padrao=""):
    return os.environ.get(nome) or getattr(config, nome, padrao)


def _norm(s):
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().lower()
    s = re.sub(r"(\d+)\s*ml", r"\1ml", s)          # "120 ml" -> "120ml" (volume vira 1 token)
    toks = [t for t in re.split(r"[^a-z0-9]+", s) if t]
    return [t for t in toks if t not in _STOP]


def ids_shopify(produto):
    """Identificadores Shopify do produto (id, handle, variantes, SKUs)."""
    ids = []
    for k in ("id", "handle", "retailer_id", "sku"):
        if produto.get(k):
            ids.append(str(produto[k]))
    for v in (produto.get("variants") or []):
        if isinstance(v, dict):
            for k in ("id", "sku"):
                if v.get(k):
                    ids.append(str(v[k]))
    return ids


_cache = None


def produtos_catalogo():
    global _cache
    if _cache is not None:
        return _cache
    cid, tok = _cfg("CATALOG_ID"), _cfg("PAGE_ACCESS_TOKEN")
    out = []
    url = f"{API}/{cid}/products"
    params = {"fields": "id,name,retailer_id", "limit": 200, "access_token": tok}
    for _ in range(10):
        r = requests.get(url, params=params, timeout=30).json()
        if "error" in r:
            print("aviso shopping:", r["error"].get("message")); break
        out += r.get("data", [])
        nxt = r.get("paging", {}).get("next")
        if not nxt:
            break
        url, params = nxt, None
    _cache = out
    return out


def product_id_para(nome, retailer_ids=None):
    prods = produtos_catalogo()
    if not prods:
        return None
    # 1) por retailer_id (exato/contido) -> distingue 30ml, 120ml e kit com certeza
    if retailer_ids:
        cand = [str(x).lower() for x in retailer_ids if x]
        for p in prods:
            rid = str(p.get("retailer_id", "")).lower()
            if rid and any(c == rid or (len(c) > 4 and (c in rid or rid in c)) for c in cand):
                return p["id"]
    # 2) por nome COM volume (limao 120ml != limao 30ml)
    a = set(_norm(nome))
    melhor, ms = None, 0.0
    for p in prods:
        b = set(_norm(p.get("name", "")))
        if not a or not b:
            continue
        score = len(a & b) / len(a | b)
        if score > ms:
            ms, melhor = score, p["id"]
    return melhor if ms >= 0.5 else None


def tags_para(nome, retailer_ids=None, x=0.5, y=0.5):
    pid = product_id_para(nome, retailer_ids)
    return [{"product_id": pid, "x": x, "y": y}] if pid else None
