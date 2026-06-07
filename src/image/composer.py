"""
Recorte do produto real (rótulo nunca alterado por IA).
Usa rembg quando disponível; senão, recorte por fundo claro de qualidade,
com alpha PARCIAL para splashes translúcidos (some o fundo branco do splash)
e produto sólido preservado (não fura o rótulo).
"""
import io

import numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage


def _cor_fundo(arr: np.ndarray, faixa: int = 12) -> np.ndarray:
    """Cor do fundo: média dos pixels CLAROS da faixa de borda (ignora o produto
    quando ele toca a borda). Fotos de e-commerce têm fundo claro/branco."""
    topo = arr[:faixa].reshape(-1, 3)
    base = arr[-faixa:].reshape(-1, 3)
    esq = arr[:, :faixa].reshape(-1, 3)
    dir = arr[:, -faixa:].reshape(-1, 3)
    borda = np.concatenate([topo, base, esq, dir])
    lum = borda.mean(axis=1)
    claros = borda[lum > 200]
    if len(claros) > len(borda) * 0.05:
        return claros.mean(axis=0)
    return np.median(borda, axis=0)


def _recorte_rembg(dados: bytes) -> Image.Image:
    from rembg import remove
    return Image.open(io.BytesIO(remove(dados))).convert("RGBA")


def _recorte_fundo(dados: bytes, tol: int = 38) -> Image.Image:
    """Recorte por fundo claro: produto sólido opaco + splash translúcido."""
    img = Image.open(io.BytesIO(dados)).convert("RGB")
    arr = np.asarray(img).astype(np.float32)
    h, w, _ = arr.shape

    fundo = _cor_fundo(arr)
    dist = np.sqrt(((arr - fundo) ** 2).sum(axis=2))

    # candidato a fundo: apenas perto da cor do fundo (NÃO marca interior do
    # produto). O flood fill abaixo só remove o que conecta às bordas.
    candidato = dist <= tol
    marca = np.zeros((h, w), bool)
    marca[0, :] = marca[-1, :] = marca[:, 0] = marca[:, -1] = True
    rot, _ = ndimage.label(candidato)
    ids = np.unique(rot[candidato & marca]); ids = ids[ids != 0]
    fundo_ext = np.isin(rot, ids)

    nao_fundo = ~fundo_ext
    corpo = ndimage.binary_dilation(ndimage.binary_erosion(nao_fundo, iterations=6), iterations=6)

    alpha = np.clip((dist - 18) / 95.0, 0, 1) ** 0.8
    alpha[corpo] = 1.0
    alpha[fundo_ext] = 0.0   # fundo conectado às bordas: totalmente transparente
    alpha = (alpha * 255).astype(np.uint8)

    # 1) erode 2px para comer a franja clara da borda
    solido = ndimage.binary_erosion(alpha > 30, iterations=2)
    alpha = np.where(solido, alpha, 0).astype(np.uint8)

    # 2) caça a franja: pixels do anel externo que continuam claros/perto do fundo -> remove
    anel = solido & ~ndimage.binary_erosion(solido, iterations=3)
    franja = anel & (dist < tol * 1.9)
    alpha[franja] = 0
    # refaz a base sólida após remover franja
    solido = alpha > 30

    # 3) suaviza a borda
    alpha_img = Image.fromarray(alpha, "L").filter(ImageFilter.GaussianBlur(0.7))

    # 4) defringe: puxa a cor do produto para uma faixa maior de borda (mata halo)
    rgb = np.asarray(img).astype(np.float32)
    dentro = ndimage.binary_erosion(solido, iterations=3)
    borda = solido & ~dentro
    for c in range(3):
        canal = rgb[:, :, c]
        canal_in = np.where(dentro, canal, 0)
        dil = ndimage.grey_dilation(canal_in, size=(9, 9))
        canal[borda] = dil[borda]
        rgb[:, :, c] = canal
    rgba = Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8), "RGB").convert("RGBA")
    rgba.putalpha(alpha_img)
    return rgba


def recortar_produto(dados: bytes, usar_ia: bool = True) -> Image.Image:
    if usar_ia:
        try:
            return _recorte_rembg(dados)
        except Exception:
            pass
    return _recorte_fundo(dados)


def bbox_conteudo(rgba: Image.Image) -> Image.Image:
    bbox = rgba.split()[-1].getbbox()
    return rgba.crop(bbox) if bbox else rgba


def sombra(produto: Image.Image, blur: int = 18, op: int = 120) -> Image.Image:
    alpha = produto.split()[-1]
    s = Image.new("RGBA", produto.size, (0, 0, 0, 0))
    s.paste(Image.new("RGBA", produto.size, (0, 0, 0, op)), (0, 0), alpha)
    return s.filter(ImageFilter.GaussianBlur(blur))



def score_recorte(dados: bytes) -> float:
    """
    Mede o quanto a foto é "espalhada" (splash, ingredientes soltos) em vez de
    um produto compacto. Usa o preenchimento do bounding box do conteúdo:
    frasco limpo preenche bem o seu quadro (compacto); foto com splash espalha
    o conteúdo e preenche pouco. Retorna 1 - preenchimento -> MENOR = mais limpo.
    """
    img = Image.open(io.BytesIO(dados)).convert("RGB")
    arr = np.asarray(img).astype(np.float32)
    fundo = _cor_fundo(arr)
    dist = np.sqrt(((arr - fundo) ** 2).sum(axis=2))
    naofundo = ndimage.binary_opening(dist > 35, iterations=2)
    area = int(naofundo.sum())
    if area == 0:
        return 1.0
    ys, xs = np.where(naofundo)
    bbox_area = (ys.max() - ys.min() + 1) * (xs.max() - xs.min() + 1)
    preenchimento = area / bbox_area
    return float(1.0 - preenchimento)

# Cenários (prompt para a IA gerar o FUNDO, sem produto) — fundo rico e premium
CENARIOS = [
    "fundo escuro premium de natureza com folhagens verdes desfocadas e luz dourada suave em bokeh, atmosfera orgânica e elegante, SEM nenhum produto, centro com espaço livre, vertical",
    "fundo escuro de madeira rústica com folhas e luz quente difusa em bokeh dourado, clima natural e aconchegante, SEM produto, centro livre, vertical",
    "fundo escuro de floresta amazônica desfocada com raios de luz dourada de fim de tarde, partículas brilhantes, SEM produto, espaço central livre, vertical",
    "fundo escuro elegante tom verde e marrom com folhas tropicais desfocadas e brilho dourado suave, SEM produto, centro livre, vertical",
]


def escolher_cenario(indice: int) -> str:
    return CENARIOS[indice % len(CENARIOS)]
