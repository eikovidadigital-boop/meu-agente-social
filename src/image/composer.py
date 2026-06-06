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


def _recorte_rembg(dados: bytes) -> Image.Image:
    from rembg import remove
    return Image.open(io.BytesIO(remove(dados))).convert("RGBA")


def _recorte_fundo(dados: bytes, tol: int = 38) -> Image.Image:
    """Recorte por fundo claro: produto sólido opaco + splash translúcido."""
    img = Image.open(io.BytesIO(dados)).convert("RGB")
    arr = np.asarray(img).astype(np.float32)
    h, w, _ = arr.shape

    s = 8
    cantos = np.concatenate([arr[:s, :s].reshape(-1, 3), arr[:s, -s:].reshape(-1, 3),
                             arr[-s:, :s].reshape(-1, 3), arr[-s:, -s:].reshape(-1, 3)])
    fundo = cantos.mean(axis=0)
    dist = np.sqrt(((arr - fundo) ** 2).sum(axis=2))

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
    sel = fundo_ext & ~corpo
    alpha[sel] = np.minimum(alpha[sel], np.clip((dist[sel] - 30) / 90.0, 0, 1))
    alpha = (alpha * 255).astype(np.uint8)
    alpha_img = Image.fromarray(alpha, "L").filter(ImageFilter.GaussianBlur(0.8))

    rgba = img.convert("RGBA"); rgba.putalpha(alpha_img)
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
    Mede o quanto a imagem é DIFÍCIL de recortar por splash branco/cinza
    (claro + pouca cor + diferente do fundo). Menor = mais limpa = melhor.
    Splash COLORIDO não é penalizado (recorta bem). Serve para escolher,
    entre as fotos de um produto, a melhor para o post.
    """
    img = Image.open(io.BytesIO(dados)).convert("RGB")
    arr = np.asarray(img).astype(np.float32)
    mx = arr.max(axis=2); mn = arr.min(axis=2)
    lum = arr.mean(axis=2)
    sat = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1), 0)
    s = 8
    cantos = np.concatenate([arr[:s, :s].reshape(-1, 3), arr[:s, -s:].reshape(-1, 3),
                             arr[-s:, :s].reshape(-1, 3), arr[-s:, -s:].reshape(-1, 3)])
    fundo = cantos.mean(axis=0)
    dist = np.sqrt(((arr - fundo) ** 2).sum(axis=2))
    problema = (lum > 170) & (sat < 0.18) & (dist > 15) & (dist < 90)
    return float(problema.mean())

# Cenários (prompt para a IA gerar o FUNDO, sem produto) — fundo rico e premium
CENARIOS = [
    "fundo escuro premium de natureza com folhagens verdes desfocadas e luz dourada suave em bokeh, atmosfera orgânica e elegante, SEM nenhum produto, centro com espaço livre, vertical",
    "fundo escuro de madeira rústica com folhas e luz quente difusa em bokeh dourado, clima natural e aconchegante, SEM produto, centro livre, vertical",
    "fundo escuro de floresta amazônica desfocada com raios de luz dourada de fim de tarde, partículas brilhantes, SEM produto, espaço central livre, vertical",
    "fundo escuro elegante tom verde e marrom com folhas tropicais desfocadas e brilho dourado suave, SEM produto, centro livre, vertical",
]


def escolher_cenario(indice: int) -> str:
    return CENARIOS[indice % len(CENARIOS)]
