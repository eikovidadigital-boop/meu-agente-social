"""
2º Layout EikoVida — estilo INFORMATIVO / PREMIUM (claro, épico)
Mantém as cores da marca (verde/creme/marrom) com pegada premium:
produto GIGANTE como herói, glow dourado atrás, selo PREMIUM com estrelas
e faixa de frete. Assinatura de montar() inalterada (não quebra o pipeline).

REGRAS:
- Respeita o FOCO do post: PELE, CABELO ou SAUDE (textos já chegam filtrados).
- Reforça que o óleo é PURO (faixa "100% PURO E NATURAL").
- Frasco dimensionado "cabe numa caixa" -> serve 120ml (alto), 30ml (baixo) e kit (largo).
"""
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import numpy as np
import math
import os

W, H = 1080, 1350
VERDE  = (135, 173, 37)
VERDE_ESC = (104, 134, 24)
MARROM = (93, 64, 55)
MARROM_ESC = (61, 41, 35)
CREME  = (245, 240, 225)
BRANCO = (255, 255, 255)
DOURADO = (201, 162, 77)
DOURADO_CLARO = (255, 226, 150)

_RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_FONTES = os.path.join(_RAIZ, "assets", "fontes")
ANTON = os.path.join(_FONTES, "Anton.ttf")
MONT  = os.path.join(_FONTES, "Montserrat.ttf")

FOCO_LABEL = {"PELE": "PARA A PELE", "CABELO": "PARA OS CABELOS", "SAUDE": "PARA A SAÚDE"}


def mont(size, weight=600):
    f = ImageFont.truetype(MONT, size)
    try:
        f.set_variation_by_axes([weight])
    except Exception:
        pass
    return f


def anton(size):
    return ImageFont.truetype(ANTON, size)


def texto_tracking(draw, y, txt, font, fill, tracking=0, center=W//2):
    larg = sum(draw.textlength(c, font=font) + tracking for c in txt) - tracking
    x = center - larg/2
    for c in txt:
        draw.text((x, y), c, font=font, fill=fill); x += draw.textlength(c, font=font) + tracking


def quebrar(d, txt, font, maxw):
    out, cur = [], ""
    for p in txt.split():
        t = (cur + " " + p).strip()
        if d.textlength(t, font=font) > maxw and cur:
            out.append(cur); cur = p
        else:
            cur = t
    if cur:
        out.append(cur)
    return out


# ---------- elementos premium ----------
def _glow(cx, cy, raio, cor=DOURADO_CLARO):
    """Brilho radial dourado (épico) atrás do produto."""
    yy, xx = np.ogrid[0:H, 0:W]
    dist = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2)
    a = np.clip(1 - dist / raio, 0, 1) ** 2
    alpha = (a * 205).astype(np.uint8)
    return Image.fromarray(alpha, "L")


def _estrela_pts(cx, cy, r):
    pts = []
    for i in range(10):
        ang = -math.pi/2 + i*math.pi/5
        rr = r if i % 2 == 0 else r*0.42
        pts.append((cx + rr*math.cos(ang), cy + rr*math.sin(ang)))
    return pts


def desenhar_estrela(d, cx, cy, r, fill):
    d.polygon(_estrela_pts(cx, cy, r), fill=fill)


def badge_premium(d, x, y):
    """Selo PREMIUM com 5 estrelas (estilo do post do Paulo)."""
    w, h = 234, 92
    d.rounded_rectangle([x, y, x+w, y+h], radius=18, fill=MARROM_ESC)
    d.rounded_rectangle([x+4, y+4, x+w-4, y+h-4], radius=14, outline=DOURADO, width=2)
    d.text((x+w/2, y+27), "PREMIUM", font=mont(25, 800), fill=DOURADO_CLARO, anchor="mm")
    sx = x + w/2 - 2*22
    for i in range(5):
        desenhar_estrela(d, sx + i*22, y+62, 10, DOURADO)


def faixa_frete(d, x, y):
    """Faixa 'ENVIAMOS PARA TODO O BRASIL' com caminhãozinho."""
    w, h = 336, 60
    d.rounded_rectangle([x, y, x+w, y+h], radius=14, fill=VERDE_ESC)
    c0 = x + 18
    d.rectangle([c0, y+24, c0+26, y+40], fill=BRANCO)
    d.polygon([(c0+26, y+29), (c0+38, y+29), (c0+43, y+40), (c0+26, y+40)], fill=BRANCO)
    d.ellipse([c0+3, y+38, c0+13, y+48], fill=MARROM_ESC)
    d.ellipse([c0+30, y+38, c0+40, y+48], fill=MARROM_ESC)
    d.text((c0+58, y + h/2), "ENVIAMOS P/ TODO BRASIL", font=mont(16, 800), fill=BRANCO, anchor="lm")


def desenhar_check(d, cx, cy, r):
    d.ellipse([cx-r, cy-r, cx+r, cy+r], fill=VERDE)
    d.line([(cx-r*0.45, cy), (cx-r*0.1, cy+r*0.4)], fill=BRANCO, width=max(3, int(r*0.22)))
    d.line([(cx-r*0.1, cy+r*0.4), (cx+r*0.5, cy-r*0.45)], fill=BRANCO, width=max(3, int(r*0.22)))


def pill(d, cx, y, txt, font, h=56):
    larg = d.textlength(txt, font=font) + 56; x0 = cx-larg/2; x1 = cx+larg/2
    d.rounded_rectangle([x0, y, x1, y+h], radius=h//2, outline=MARROM, width=3)
    d.text((cx, y+h/2), txt, font=font, fill=MARROM, anchor="mm"); return larg


def badge_foco(d, x, y, foco):
    txt = FOCO_LABEL.get(foco, ""); f = mont(22, 800)
    larg = d.textlength(txt, font=f) + 44; h = 50
    d.rounded_rectangle([x, y, x+larg, y+h], radius=h//2, fill=VERDE)
    d.text((x+larg/2, y+h/2), txt, font=f, fill=BRANCO, anchor="mm"); return h


# ---------- FRASCO PLACEHOLDER (só para o mockup) ----------
def frasco_demo(volume="120 ml"):
    s = 4
    curto = volume.strip().startswith("30")
    bw_mm, bh_mm = (290, 640) if not curto else (290, 380)
    w, h = 380*s, 820*s
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(img); cx = w//2
    top = (h - bh_mm*s) - 10*s
    arr = np.zeros((h, w, 4), dtype=np.uint8)
    for yy in range(top, h):
        t = (yy-top)/max(1, (h-top)); r = int(196-40*t); g = int(112-30*t); b = int(38-12*t)
        arr[yy, :] = (r, g, b, 255)
    grad = Image.fromarray(arr, "RGBA")
    body = Image.new("L", (w, h), 0); bd = ImageDraw.Draw(body)
    bd.rounded_rectangle([cx-bw_mm*s//2, top, cx+bw_mm*s//2, h-8*s], radius=68*s, fill=255)
    img.paste(grad, (0, 0), body)
    d = ImageDraw.Draw(img)
    tw = 150*s
    d.rounded_rectangle([cx-tw//2, top-90*s, cx+tw//2, top-2*s], radius=14*s, fill=(28, 24, 22, 255))
    d.rectangle([cx-52*s, top-12*s, cx+52*s, top+28*s], fill=(150, 92, 40, 255))
    sh = Image.new("RGBA", (w, h), (0, 0, 0, 0)); sd = ImageDraw.Draw(sh)
    sd.rounded_rectangle([cx-bw_mm*s//2+18*s, top+20*s, cx-bw_mm*s//2+62*s, h-40*s], radius=40*s, fill=(255, 255, 255, 70))
    img = Image.alpha_composite(img, sh.filter(ImageFilter.GaussianBlur(10*s)))
    d = ImageDraw.Draw(img)
    lab_h = int(bh_mm*s*0.34); lab_t = h - 8*s - lab_h - 28*s
    d.rounded_rectangle([cx-114*s, lab_t, cx+114*s, lab_t+lab_h], radius=16*s, fill=CREME+(255,))
    d.rectangle([cx-114*s, lab_t+8*s, cx+114*s, lab_t+16*s], fill=VERDE+(255,))
    d.text((cx, lab_t+lab_h*0.30), "EIKO", font=anton(int(lab_h*0.26)), fill=MARROM_ESC+(255,), anchor="mm")
    d.text((cx, lab_t+lab_h*0.60), "ÓLEO VEGETAL", font=mont(int(lab_h*0.095), 700), fill=VERDE_ESC+(255,), anchor="mm")
    d.text((cx, lab_t+lab_h*0.82), volume, font=mont(int(lab_h*0.11), 600), fill=MARROM+(255,), anchor="mm")
    return img.resize((380, 820), Image.LANCZOS)


# ---------- LAYOUT ----------
def montar(produto_rgba, nome, foco, tagline3, descricao, beneficios3,
           volume="120 ml", eh_kit=False):
    # fundo creme com leve textura
    img = Image.new("RGB", (W, H), CREME)
    noise = (np.random.rand(H, W, 1)*8).astype(np.uint8)
    img = Image.fromarray(np.clip(np.array(img).astype(np.int16)-4+noise, 0, 255).astype(np.uint8), "RGB")

    # ---- PRODUTO HERÓI: dimensiona primeiro (pra posicionar o glow atrás) ----
    pr = produto_rgba.copy()
    cox, coy = pr.size
    max_h, max_w = 880, 560          # GIGANTE (era 770x440)
    esc = min(max_w/cox, max_h/coy)
    pr = pr.resize((max(1, int(cox*esc)), max(1, int(coy*esc))), Image.LANCZOS)
    pw, ph = pr.size
    fx = W - pw - 48                 # colado à direita (igual ao post do Paulo)
    fy = H - ph - 132

    # GLOW dourado épico, centrado no produto
    gx, gy = fx + pw//2, fy + int(ph*0.46)
    mask = _glow(gx, gy, raio=560)
    img.paste(Image.new("RGB", (W, H), (255, 216, 128)), (0, 0), mask)

    d = ImageDraw.Draw(img)

    # FAIXA TOPO (pureza)
    d.rectangle([0, 0, W, 72], fill=VERDE)
    texto_tracking(d, 23, "100% PURO E NATURAL  •  PRENSADO A FRIO", mont(24, 700), BRANCO, tracking=4)

    mx = 64
    badge_foco(d, mx, 100, foco)

    # NOME grande (coluna esquerda)
    fn = anton(80); asc = fn.getbbox("AÇ")[3]
    y = 172
    for ln in quebrar(d, nome.upper(), fn, 600):
        d.text((mx, y), ln, font=fn, fill=MARROM_ESC); y += asc + 10
    # tagline
    y += 6
    d.text((mx, y), "  •  ".join(t.upper() for t in tagline3), font=mont(25, 700), fill=VERDE_ESC); y += 50

    # SOMBRA rica + PRODUTO
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0)); sd = ImageDraw.Draw(sh)
    sd.ellipse([fx+pw*0.10, fy+ph-50, fx+pw*0.90, fy+ph+34], fill=(50, 34, 24, 150))
    img.paste(Image.new("RGB", (W, H), (45, 30, 22)), (0, 0),
              sh.filter(ImageFilter.GaussianBlur(26)).split()[3])
    img.paste(pr, (fx, fy), pr)
    d = ImageDraw.Draw(img)

    # SELO PREMIUM + FRETE (canto superior direito)
    badge_premium(d, W-258, 100)
    faixa_frete(d, W-360, 208)

    # BENEFÍCIOS (coluna esquerda)
    by = max(y + 26, 470)
    d.text((mx, by), "BENEFÍCIOS", font=mont(25, 800), fill=MARROM)
    d.line([(mx, by+40), (mx+140, by+40)], fill=VERDE, width=4); by += 68
    fb = mont(27, 600)
    for b in beneficios3:
        desenhar_check(d, mx+15, by+14, 15); ty = by
        for l in quebrar(d, b, fb, 360):
            d.text((mx+44, ty), l, font=fb, fill=MARROM_ESC); ty += 34
        by = ty + 20

    # SELOS (rodapé esquerda)
    fp = mont(21, 700)
    def linha_selos(itens, yy):
        x = mx
        for s in itens:
            larg = d.textlength(s, font=fp)+50
            pill(d, x+larg/2, yy, s, fp, h=52); x += larg + 16
    linha_selos(["100% PURO", "VEGANO"], H-256)
    linha_selos(["SEM PARABENOS", "CRUELTY FREE"], H-186)

    # RODAPÉ
    d.rectangle([0, H-90, W, H], fill=MARROM)
    texto_tracking(d, H-62, "BELEZA QUE VEM DA NATUREZA", mont(28, 700), CREME, tracking=6)
    return img


def escolher_layout(eh_kit, indice):
    return "dramatico" if indice % 2 == 0 else "informativo"
