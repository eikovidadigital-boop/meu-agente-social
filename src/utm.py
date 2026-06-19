# -*- coding: utf-8 -*-
"""
Etiqueta de rastreamento (UTM) nos links que o sistema publica.
Com isso, no Shopify/Google Analytics da pra ver EXATAMENTE quais posts,
comentarios e produtos trouxeram visita e venda — em vez de publicar no escuro.

Uso:
    utm.aplicar("https://eikovida.com/products/oleo-de-coco", "comentario")
    -> https://eikovida.com/products/oleo-de-coco?utm_source=instagram&utm_medium=comentario&utm_campaign=oleo-de-coco
"""
import re
import unicodedata
from urllib.parse import urlparse, parse_qsl, urlencode, urlunparse


def _slug(s):
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().lower()
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s or "produto"


def _campanha_do_link(url):
    """Tira o nome do produto do proprio link (.../products/<slug>)."""
    m = re.search(r"/products/([^/?#]+)", url or "")
    return _slug(m.group(1)) if m else "geral"


def aplicar(url, medium="instagram", campaign=None, source="instagram"):
    """Adiciona utm_source/medium/campaign ao link, sem duplicar nem quebrar
    parametros que ja existam. Links que nao sejam http voltam intactos."""
    if not url or not str(url).startswith("http"):
        return url
    u = urlparse(url)
    q = dict(parse_qsl(u.query))
    q.setdefault("utm_source", source)
    q.setdefault("utm_medium", medium)
    q.setdefault("utm_campaign", _slug(campaign) if campaign else _campanha_do_link(url))
    return urlunparse(u._replace(query=urlencode(q)))
