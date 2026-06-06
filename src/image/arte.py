"""
Arte do post (camada visual em cima do fundo).
Monta o post 4:5 (1080x1350): FUNDO (gerado por IA, ou bokeh de reserva)
+ PRODUTO real recortado + TÍTULO 3D dourado em placa + SELO de benefício
com seta + TAGLINE + LOGO. Textos vêm prontos (gerados pelo agente).
Nada do produto é alterado por IA.
"""
import io

import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

from src import config
from src.image import composer

W, H = 1080, 1350
CREME = (245, 240, 225)
VERDE_CLARO = (167, 209, 60)


def _fz(path, t):
    return ImageFont.truetype(str(path), t)


def _grad(size, ct, cb):
    w, h = size
    g = Image.new("RGB", (1, h))
    for y in range(h):
        f = y / max(1, h - 1)
        g.putpixel((0, y), tuple(int(ct[i] * (1 - f) + cb[i] * f) for i in range(3)))
    return g.resize((w, h))


def _fundo_reserva(seed):
    base = _grad((W, H), (38, 30, 18), (16, 13, 8)).convert("RGBA")
    bok = Image.new("RGBA", (W, H), (0, 0, 0, 0)); bd = ImageDraw.Draw(bok)
    rng = np.random.default_rng(seed)
    for _ in range(38):
        cx, cy = rng.integers(0, W), rng.integers(0, H); r = rng.integers(20, 70)
        col = (255, 200, 90) if rng.random() < 0.6 else VERDE_CLARO
        bd.ellipse([cx - r, cy - r, cx + r, cy + r], fill=col + (int(rng.integers(20, 50)),))
    base.alpha_composite(bok.filter(ImageFilter.GaussianBlur(14)))
    v = Image.new("L", (W, H), 0)
    ImageDraw.Draw(v).ellipse([-W * 0.2, -H * 0.15, W * 1.2, H * 1.15], fill=255)
    return Image.composite(base, Image.new("RGBA", (W, H), (0, 0, 0, 255)),
                           v.filter(ImageFilter.GaussianBlur(220)))


def _preparar_fundo(fundo_img, seed):
    """Usa o fundo da IA (cobre 1080x1350) escurecido p/ contraste; senão, reserva."""
    if fundo_img is None:
        return _fundo_reserva(seed)
    f = fundo_img.convert("RGB")
    # cobre o canvas mantendo proporção (cover)
    escala = max(W / f.width, H / f.height)
    f = f.resize((int(f.width * escala), int(f.height * escala)))
    x = (f.width - W) // 2; y = (f.height - H) // 2
    f = f.crop((x, y, x + W, y + H)).convert("RGBA")
    # escurece p/ o texto e o produto se destacarem + vinheta
    f.alpha_composite(Image.new("RGBA", (W, H), (0, 0, 0, 90)))
    v = Image.new("L", (W, H), 0)
    ImageDraw.Draw(v).ellipse([-W * 0.25, -H * 0.2, W * 1.25, H * 1.2], fill=255)
    return Image.composite(f, Image.new("RGBA", (W, H), (0, 0, 0, 255)),
                           v.filter(ImageFilter.GaussianBlur(200)))


def _placa(base, box, r=22):
    x0, y0, x1, y1 = box
    mad = _grad((x1 - x0, y1 - y0), (74, 48, 26), (46, 28, 14)).convert("RGBA")
    m = Image.new("L", mad.size, 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, x1 - x0 - 1, y1 - y0 - 1], radius=r, fill=255)
    sob = Image.new("RGBA", base.size, (0, 0, 0, 0))
    ImageDraw.Draw(sob).rounded_rectangle([x0 - 6, y0 - 6, x1 + 6, y1 + 6], radius=r + 6, fill=(0, 0, 0, 150))
    base.alpha_composite(sob.filter(ImageFilter.GaussianBlur(8)))
    base.paste(mad, (x0, y0), m)
    ImageDraw.Draw(base).rounded_rectangle([x0, y0, x1, y1], radius=r, outline=(150, 110, 60, 255), width=3)


def _titulo_3d(base, xy, txt, fnt, prof=14, anchor="ma"):
    x, y = xy
    tmp = Image.new("RGBA", base.size, (0, 0, 0, 0)); td = ImageDraw.Draw(tmp)
    for dx in range(-4, 5):
        for dy in range(-4, 5):
            if dx * dx + dy * dy <= 16:
                td.text((x + dx, y + dy), txt, font=fnt, fill=(45, 25, 8, 255), anchor=anchor)
    for i in range(prof, 0, -1):
        td.text((x + i * 0.6, y + i * 0.85), txt, font=fnt, fill=(110, 62, 18, 255), anchor=anchor)
    mask = Image.new("L", base.size, 0)
    ImageDraw.Draw(mask).text((x, y), txt, font=fnt, fill=255, anchor=anchor)
    tmp = Image.composite(_grad(base.size, (255, 242, 150), (232, 165, 38)).convert("RGBA"), tmp, mask)
    bril = Image.new("L", base.size, 0)
    ImageDraw.Draw(bril).text((x, y - 3), txt, font=fnt, fill=255, anchor=anchor)
    bril = Image.composite(bril, Image.new("L", base.size, 0), mask).filter(ImageFilter.GaussianBlur(1))
    tmp = Image.composite(Image.new("RGBA", base.size, (255, 252, 225, 255)), tmp, bril.point(lambda v: int(v * 0.5)))
    base.alpha_composite(tmp)


def _logo():
    """Carrega o logo preservando as letras. Usa a transparência nativa do PNG;
    só remove fundo branco se o PNG não tiver transparência (flood das bordas,
    para nunca apagar as letras brancas internas)."""
    try:
        img = Image.open(config.LOGO_PATH).convert("RGBA")
        arr = np.asarray(img)
        if (arr[:, :, 3] == 0).mean() > 0.08:
            return img  # já tem fundo transparente — usa direto (letras intactas)
        from scipy import ndimage
        rgb = arr[:, :, :3]
        branco = (rgb[:, :, 0] > 235) & (rgb[:, :, 1] > 235) & (rgb[:, :, 2] > 235)
        h, w = branco.shape
        marca = np.zeros((h, w), bool)
        marca[0, :] = marca[-1, :] = marca[:, 0] = marca[:, -1] = True
        rot, _ = ndimage.label(branco)
        ids = np.unique(rot[branco & marca]); ids = ids[ids != 0]
        out = arr.copy(); out[np.isin(rot, ids), 3] = 0
        return Image.fromarray(out, "RGBA")
    except Exception:
        return None


def _fit_fonte(texto, fonte_path, tam_max, larg_max):
    """Reduz a fonte até o texto caber na largura."""
    t = tam_max
    while t > 22:
        f = _fz(fonte_path, t)
        if f.getbbox(texto)[2] <= larg_max:
            return f
        t -= 4
    return _fz(fonte_path, t)


def montar(produto_bytes: bytes, textos: dict, fundo_img: Image.Image = None,
           seed: int = 0, usar_ia_recorte: bool = True) -> bytes:
    """
    textos = {
      "titulo": "ÓLEO DE PEQUI",
      "subtitulo": "ENERGIA E VITALIDADE DA NATUREZA",
      "beneficio": ["RICO EM", "VITAMINA A", "E CAROTENOS"],   # 3 linhas
      "tagline": ["100% NATURAL", "PRENSADO A FRIO"],          # 2 linhas
    }
    """
    base = _preparar_fundo(fundo_img, seed)

    # produto recortado, centralizado
    rgba = composer.bbox_conteudo(composer.recortar_produto(produto_bytes, usar_ia=usar_ia_recorte))
    ph = int(H * 0.50); pw = int(rgba.width * ph / rgba.height)
    prod = rgba.resize((pw, ph))
    px = W // 2 - pw // 2; py = int(H * 0.80) - ph
    base.alpha_composite(composer.sombra(prod), (px + 12, py + 18))
    base.alpha_composite(prod, (px, py))

    # título em placa (centralizado)
    _placa(base, [70, 65, W - 70, 320])
    f_tit = _fit_fonte(textos["titulo"], config.FONTE_TITULO, 118, W - 200)
    _titulo_3d(base, (W // 2, 90), textos["titulo"], f_tit, prof=14)
    d = ImageDraw.Draw(base)
    f_sub = _fit_fonte(textos["subtitulo"], config.FONTE_TEXTO, 32, W - 200)
    d.text((W // 2, 250), textos["subtitulo"], font=f_sub, fill=CREME, anchor="ma")

    # QUADRO ÚNICO combinado (benefício + selo), centralizado no rodapé
    benef = " ".join([b for b in (textos.get("beneficio") or []) if b]) or "100% NATURAL"
    tag = " • ".join([t for t in (textos.get("tagline") or []) if t]) or "PRENSADO A FRIO"
    qx0, qy0, qx1, qy1 = 130, H - 220, W - 130, H - 65
    _placa(base, [qx0, qy0, qx1, qy1], r=20)
    d = ImageDraw.Draw(base)
    f_b = _fit_fonte(benef, config.FONTE_TEXTO, 46, qx1 - qx0 - 60)
    d.text((W // 2, qy0 + 30), benef, font=f_b, fill=VERDE_CLARO, anchor="ma")
    f_t = _fit_fonte(tag, config.FONTE_TITULO, 42, qx1 - qx0 - 60)
    d.text((W // 2, qy0 + 92), tag, font=f_t, fill=CREME, anchor="ma")

    buf = io.BytesIO()
    base.convert("RGB").save(buf, format="JPEG", quality=92)
    return buf.getvalue()
