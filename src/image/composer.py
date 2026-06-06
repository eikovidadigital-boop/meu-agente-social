"""
Compositor de imagens.
Monta o post juntando:
  1) o PRODUTO REAL recortado (rótulo preservado — nunca gerado por IA)
  2) um CENÁRIO atrativo (gerado por IA, sem produto, ou imagem de fundo)
Com vários LAYOUTS de posição/tamanho que se alternam, pra o feed não ficar
repetitivo.

Recorte do produto: usa rembg (recorte por IA) quando disponível; se não,
cai no recorte por fundo branco/sólido (mais leve), bom para fotos de catálogo.
"""
import io

from PIL import Image, ImageFilter

CANVAS = 1024  # post quadrado 1:1


# ---------------- Recorte do produto ----------------
def _recorte_rembg(dados: bytes):
    from rembg import remove
    saida = remove(dados)
    return Image.open(io.BytesIO(saida)).convert("RGBA")


def _recorte_fundo_solido(dados: bytes, tolerancia: int = 28) -> Image.Image:
    """Remove fundo sólido (branco) detectado pelos cantos. Para fotos de catálogo."""
    img = Image.open(io.BytesIO(dados)).convert("RGBA")
    px = img.load()
    w, h = img.size
    cantos = [px[0, 0], px[w - 1, 0], px[0, h - 1], px[w - 1, h - 1]]
    fr = sum(c[0] for c in cantos) // 4
    fg = sum(c[1] for c in cantos) // 4
    fb = sum(c[2] for c in cantos) // 4
    dados_px = img.getdata()
    novo = []
    for r, g, b, a in dados_px:
        if abs(r - fr) <= tolerancia and abs(g - fg) <= tolerancia and abs(b - fb) <= tolerancia:
            novo.append((r, g, b, 0))
        else:
            novo.append((r, g, b, a))
    img.putdata(novo)
    return img


def recortar_produto(dados: bytes, usar_ia: bool = True) -> Image.Image:
    """Recorta o produto, devolvendo RGBA com fundo transparente."""
    if usar_ia:
        try:
            return _recorte_rembg(dados)
        except Exception:
            pass  # cai no método leve
    return _recorte_fundo_solido(dados)


def _bbox_conteudo(rgba: Image.Image) -> Image.Image:
    """Corta as bordas transparentes, deixando só o produto."""
    bbox = rgba.split()[-1].getbbox()
    return rgba.crop(bbox) if bbox else rgba


# ---------------- Layouts (posição/tamanho do produto) ----------------
# escala = altura do produto relativa ao canvas; ancora = ponto de referência (0-1)
LAYOUTS = [
    {"nome": "centro_baixo",     "escala": 0.66, "cx": 0.50, "base": 0.92},
    {"nome": "esquerda",         "escala": 0.60, "cx": 0.32, "base": 0.90},
    {"nome": "direita",          "escala": 0.60, "cx": 0.68, "base": 0.90},
    {"nome": "grande_centro",    "escala": 0.78, "cx": 0.50, "base": 0.96},
    {"nome": "canto_inferior",   "escala": 0.52, "cx": 0.72, "base": 0.95},
]


def escolher_layout(indice: int) -> dict:
    return LAYOUTS[indice % len(LAYOUTS)]


def _sombra(produto: Image.Image) -> Image.Image:
    """Cria uma sombra suave a partir do recorte."""
    alpha = produto.split()[-1]
    sombra = Image.new("RGBA", produto.size, (0, 0, 0, 0))
    preto = Image.new("RGBA", produto.size, (0, 0, 0, 120))
    sombra.paste(preto, (0, 0), alpha)
    return sombra.filter(ImageFilter.GaussianBlur(18))


def compor(produto_rgba: Image.Image, fundo: Image.Image, layout: dict,
           com_sombra: bool = True) -> bytes:
    """Junta produto + cenário num quadrado 1024 e devolve JPEG (bytes)."""
    fundo = fundo.convert("RGB").resize((CANVAS, CANVAS))
    canvas = fundo.convert("RGBA")

    prod = _bbox_conteudo(produto_rgba)
    alvo_h = int(CANVAS * layout["escala"])
    prop = alvo_h / prod.height
    prod = prod.resize((max(1, int(prod.width * prop)), alvo_h))

    cx = int(CANVAS * layout["cx"])
    base_y = int(CANVAS * layout["base"])
    x = cx - prod.width // 2
    y = base_y - prod.height

    if com_sombra:
        sombra = _sombra(prod)
        canvas.alpha_composite(sombra, (x + 12, y + 18))
    canvas.alpha_composite(prod, (x, y))

    buf = io.BytesIO()
    canvas.convert("RGB").save(buf, format="JPEG", quality=90)
    return buf.getvalue()


# ---------------- Cenários (prompts pra IA gerar o fundo, SEM produto) ----------------
CENARIOS = [
    "fundo de bancada de madeira clara com folhas verdes desfocadas ao redor, luz natural suave, estilo natural e aconchegante, SEM nenhum produto ou objeto no centro, espaço vazio",
    "fundo de spa minimalista, pedras e toalha branca, tons neutros e verdes, luz suave difusa, SEM produto, espaço central livre",
    "fundo de mármore branco com plantas tropicais nas laterais, iluminação clara e elegante, SEM produto, centro vazio",
    "fundo de natureza amazônica desfocada, folhagens verdes e luz dourada de fim de tarde, atmosfera orgânica, SEM produto, espaço central livre",
    "fundo de banheiro clean e moderno, prateleira de madeira, plantinhas, tons terrosos e verdes, luz suave, SEM produto, centro livre",
]


def escolher_cenario(indice: int) -> str:
    return CENARIOS[indice % len(CENARIOS)]
