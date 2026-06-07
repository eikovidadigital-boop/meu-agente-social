# -*- coding: utf-8 -*-
"""
Escolhe a FOTO MAIS LIMPA do produto (mesma logica do feed): recorta cada
foto e mede o preenchimento do bounding box. Frasco compacto = score baixo
(melhor); foto com splash espalhado = score alto (descartada).
"""
import numpy as np


def urls_produto(produto):
    if produto.get("imagem"):
        return [produto["imagem"]]
    for k in ("imagens", "images"):
        arr = produto.get(k) or []
        if arr:
            out = []
            for x in arr:
                out.append((x.get("src") or x.get("url")) if isinstance(x, dict) else x)
            return [u for u in out if u]
    return []


def score_recorte(rgba):
    """1 - (area_do_produto / area_do_bbox). Menor = mais limpo/compacto."""
    alpha = np.array(rgba.split()[-1])
    bbox = rgba.split()[-1].getbbox()
    if not bbox:
        return 1.0
    x0, y0, x1, y1 = bbox
    area_bbox = max(1, (x1 - x0) * (y1 - y0))
    area_prod = int((alpha > 10).sum())
    return 1.0 - (area_prod / area_bbox)


def melhor_recorte(produto, get_bytes, composer, max_fotos=6):
    """Recorta cada foto e devolve o recorte (RGBA) da foto mais limpa + score."""
    melhor, melhor_score = None, 2.0
    for u in urls_produto(produto)[:max_fotos]:
        try:
            rgba = composer.bbox_conteudo(composer.recortar_produto(get_bytes(u), usar_ia=False))
            s = score_recorte(rgba)
            if s < melhor_score:
                melhor, melhor_score = rgba, s
        except Exception:
            continue
    return melhor, melhor_score
