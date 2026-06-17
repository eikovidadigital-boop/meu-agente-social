# -*- coding: utf-8 -*-
"""
Escolhe a foto certa do produto e recorta.
- Produto normal: a FOTO MAIS LIMPA (frasco compacto, sem splash) — score baixo.
- KIT/combo: a foto que mostra o CONJUNTO (mais larga), pra nao aparecer so 1 item.
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


def _eh_kit(produto):
    """Detecta kit/combo pelo nome, tipo e tags do produto."""
    partes = [str(produto.get(k, "")) for k in ("nome", "titulo", "title", "product_type", "tipo")]
    tags = produto.get("tags")
    if isinstance(tags, list):
        partes.append(" ".join(str(t) for t in tags))
    elif isinstance(tags, str):
        partes.append(tags)
    txt = " ".join(partes).lower()
    return ("kit" in txt) or ("combo" in txt)


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


def _largura_rel(rgba):
    """Largura / altura do bounding box. Maior = mais largo (= varios frascos lado a lado)."""
    bbox = rgba.split()[-1].getbbox()
    if not bbox:
        return 0.0
    x0, y0, x1, y1 = bbox
    return (x1 - x0) / max(1, (y1 - y0))


def melhor_recorte(produto, get_bytes, composer, max_fotos=6):
    """Recorta cada foto e devolve o recorte (RGBA) da foto certa + seu score.
    Kit -> foto mais larga (mostra o conjunto). Normal -> foto mais limpa."""
    eh_kit = _eh_kit(produto)
    cands = []  # (score, largura_rel, rgba)
    for u in urls_produto(produto)[:max_fotos]:
        try:
            rgba = composer.bbox_conteudo(composer.recortar_produto(get_bytes(u), usar_ia=False))
            cands.append((score_recorte(rgba), _largura_rel(rgba), rgba))
        except Exception:
            continue
    if not cands:
        return None, 2.0
    if eh_kit:
        # kit: prioriza a foto que mostra o conjunto (mais larga)
        escolhido = max(cands, key=lambda c: c[1])
    else:
        # normal: a mais limpa/compacta (menor score)
        escolhido = min(cands, key=lambda c: c[0])
    return escolhido[2], escolhido[0]
