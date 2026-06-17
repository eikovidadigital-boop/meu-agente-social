"""
2º Layout EikoVida — estilo INFORMATIVO / EDITORIAL (claro)
Diferente do layout 1 (escuro/dourado/dramatico).

REGRAS (pedidas pelo Paulo):
- Respeita o FOCO do post: PELE, CABELO ou SAUDE. Os textos (tagline,
  descricao, beneficios) ja chegam FILTRADOS por foco vindos do agente
  arte_textos.py -> este layout SO renderiza, nunca mistura beleza com saude.
- Reforca que o oleo e PURO (faixa "100% PURO E NATURAL").
- Frasco dimensionado "cabe numa caixa" -> serve 120ml (alto) e 30ml (baixo).
- NAO e usado em kits: a funcao recusa kit (kit tera layout proprio depois).
"""
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import numpy as np

W, H = 1080, 1350
VERDE  = (135, 173, 37)
VERDE_ESC = (104, 134, 24)
MARROM = (93, 64, 55)
MARROM_ESC = (61, 41, 35)
CREME  = (245, 240, 225)
BRANCO = (255, 255, 255)

import os
_RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_FONTES = os.path.join(_RAIZ, "assets", "fontes")
ANTON = os.path.join(_FONTES, "Anton.ttf")
MONT  = os.path.join(_FONTES, "Montserrat.ttf")

# rotulo visivel do foco (reforca o angulo e evita mistura)
FOCO_LABEL = {"PELE": "PARA A PELE", "CABELO": "PARA OS CABELOS", "SAUDE": "PARA A SAÚDE"}

def mont(size, weight=600):
    f = ImageFont.truetype(MONT, size); f.set_variation_by_axes([weight]); return f
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
        else: cur = t
    if cur: out.append(cur)
    return out

# ---------- FRASCO PLACEHOLDER (so para o mockup) ----------
def frasco_demo(volume="120 ml"):
    s = 4
    curto = volume.strip().startswith("30")
    bw_mm, bh_mm = (290, 640) if not curto else (290, 380)  # 30ml mais baixo
    w, h = 380*s, 820*s
    img = Image.new("RGBA", (w, h), (0,0,0,0)); d = ImageDraw.Draw(img); cx = w//2
    top = (h - bh_mm*s) - 10*s            # ancora embaixo, deixando espaco p/ tampa
    # corpo ambar com gradiente
    arr = np.zeros((h, w, 4), dtype=np.uint8)
    for yy in range(top, h):
        t = (yy-top)/max(1,(h-top)); r=int(196-40*t); g=int(112-30*t); b=int(38-12*t)
        arr[yy,:] = (r,g,b,255)
    grad = Image.fromarray(arr, "RGBA")
    body = Image.new("L", (w,h), 0); bd = ImageDraw.Draw(body)
    bd.rounded_rectangle([cx-bw_mm*s//2, top, cx+bw_mm*s//2, h-8*s], radius=68*s, fill=255)
    img.paste(grad, (0,0), body)
    d = ImageDraw.Draw(img)
    # tampa + gargalo (cabem acima do corpo)
    tw = 150*s
    d.rounded_rectangle([cx-tw//2, top-90*s, cx+tw//2, top-2*s], radius=14*s, fill=(28,24,22,255))
    d.rectangle([cx-52*s, top-12*s, cx+52*s, top+28*s], fill=(150,92,40,255))
    # brilho
    sh = Image.new("RGBA",(w,h),(0,0,0,0)); sd=ImageDraw.Draw(sh)
    sd.rounded_rectangle([cx-bw_mm*s//2+18*s, top+20*s, cx-bw_mm*s//2+62*s, h-40*s], radius=40*s, fill=(255,255,255,70))
    img = Image.alpha_composite(img, sh.filter(ImageFilter.GaussianBlur(10*s)))
    # rotulo
    d = ImageDraw.Draw(img)
    lab_h = int(bh_mm*s*0.34); lab_t = h - 8*s - lab_h - 28*s
    d.rounded_rectangle([cx-114*s, lab_t, cx+114*s, lab_t+lab_h], radius=16*s, fill=CREME+(255,))
    d.rectangle([cx-114*s, lab_t+8*s, cx+114*s, lab_t+16*s], fill=VERDE+(255,))
    d.text((cx, lab_t+lab_h*0.30), "EIKO", font=anton(int(lab_h*0.26)), fill=MARROM_ESC+(255,), anchor="mm")
    d.text((cx, lab_t+lab_h*0.60), "ÓLEO VEGETAL", font=mont(int(lab_h*0.095),700), fill=VERDE_ESC+(255,), anchor="mm")
    d.text((cx, lab_t+lab_h*0.82), volume, font=mont(int(lab_h*0.11),600), fill=MARROM+(255,), anchor="mm")
    return img.resize((380, 820), Image.LANCZOS)

# ---------- LAYOUT ----------
def desenhar_check(d, cx, cy, r):
    d.ellipse([cx-r, cy-r, cx+r, cy+r], fill=VERDE)
    d.line([(cx-r*0.45,cy),(cx-r*0.1,cy+r*0.4)], fill=BRANCO, width=max(3,int(r*0.22)))
    d.line([(cx-r*0.1,cy+r*0.4),(cx+r*0.5,cy-r*0.45)], fill=BRANCO, width=max(3,int(r*0.22)))

def pill(d, cx, y, txt, font, h=56):
    larg = d.textlength(txt, font=font) + 56; x0=cx-larg/2; x1=cx+larg/2
    d.rounded_rectangle([x0,y,x1,y+h], radius=h//2, outline=MARROM, width=3)
    d.text((cx, y+h/2), txt, font=font, fill=MARROM, anchor="mm"); return larg

def badge_foco(d, x, y, foco):
    txt = FOCO_LABEL.get(foco, ""); f = mont(22, 800)
    larg = d.textlength(txt, font=f) + 44; h = 50
    d.rounded_rectangle([x, y, x+larg, y+h], radius=h//2, fill=VERDE)
    d.text((x+larg/2, y+h/2), txt, font=f, fill=BRANCO, anchor="mm"); return h

def montar(produto_rgba, nome, foco, tagline3, descricao, beneficios3,
           volume="120 ml", eh_kit=False):
    # ---- GUARDA: este layout nao serve kit ----
    if eh_kit:
        raise ValueError("Layout informativo nao deve ser usado em kit (kit tera layout proprio).")

    img = Image.new("RGB", (W, H), CREME)
    noise = (np.random.rand(H, W, 1)*8).astype(np.uint8)
    img = Image.fromarray(np.clip(np.array(img).astype(np.int16)-4+noise, 0, 255).astype(np.uint8), "RGB")
    d = ImageDraw.Draw(img)

    # FAIXA TOPO (reforca pureza)
    d.rectangle([0,0,W,70], fill=VERDE)
    texto_tracking(d, 22, "100% PURO E NATURAL  •  PRENSADO A FRIO", mont(24,700), BRANCO, tracking=4)

    mx = 70
    # badge de foco (deixa o angulo explicito -> nunca mistura)
    badge_foco(d, mx, 104, foco)
    # nome grande: nome completo do produto (ja traz o tipo correto). NUNCA forca "Óleo de",
    # pra um condicionador/mascara nunca virar "óleo".
    fn = anton(84); asc = fn.getbbox("AÇ")[3]
    y = 178
    for ln in quebrar(d, nome.upper(), fn, W-mx*2):
        d.text((mx, y), ln, font=fn, fill=MARROM_ESC); y += asc + 12
    # tagline
    y += 8
    d.text((mx, y), "  •  ".join(t.upper() for t in tagline3), font=mont(27,700), fill=VERDE); y += 54
    # descricao curta
    fdesc = mont(26,500)
    for ln in quebrar(d, descricao, fdesc, W-mx*2-470):
        d.text((mx, y), ln, font=fdesc, fill=(80,66,60)); y += 36

    # FRASCO (direita) -- "cabe numa caixa": limita altura E largura
    pr = produto_rgba.copy()
    cox, coy = pr.size
    max_h, max_w = 770, 440          # frasco maior (ocupa mais o post)
    esc = min(max_w/cox, max_h/coy)
    pr = pr.resize((max(1,int(cox*esc)), max(1,int(coy*esc))), Image.LANCZOS)
    pw, ph = pr.size
    fx = W - pw - 70; fy = H - ph - 175
    sh = Image.new("RGBA",(W,H),(0,0,0,0)); sd=ImageDraw.Draw(sh)
    sd.ellipse([fx+pw*0.12, fy+ph-45, fx+pw*0.88, fy+ph+30], fill=(60,40,30,120))
    img.paste(Image.new("RGB",(W,H),(0,0,0)), (0,0), sh.filter(ImageFilter.GaussianBlur(22)).split()[3])
    img.paste(pr, (fx, fy), pr); d = ImageDraw.Draw(img)

    # BENEFICIOS (esquerda) -- ja filtrados pelo foco
    by = y + 44
    d.text((mx, by), "BENEFÍCIOS", font=mont(26,800), fill=MARROM)
    d.line([(mx, by+44),(mx+150, by+44)], fill=VERDE, width=4); by += 80
    fb = mont(29,600)
    for b in beneficios3:
        desenhar_check(d, mx+16, by+15, 16); ty = by
        for l in quebrar(d, b, fb, 400):
            d.text((mx+48, ty), l, font=fb, fill=MARROM_ESC); ty += 37
        by = ty + 22

    # SELOS
    fp = mont(22,700); py = H-250; px = mx
    for s in ["100% PURO", "VEGANO"]:
        px += pill(d, px+(d.textlength(s,font=fp)+56)/2, py, s, fp) + 18 if False else 0
    # desenha selos em duas linhas, alinhados a esquerda
    def linha_selos(itens, yy):
        x = mx
        for s in itens:
            larg = d.textlength(s, font=fp)+56
            pill(d, x+larg/2, yy, s, fp); x += larg + 18
    linha_selos(["100% PURO", "VEGANO"], H-250)
    linha_selos(["SEM PARABENOS", "CRUELTY FREE"], H-176)

    # RODAPE
    d.rectangle([0,H-90,W,H], fill=MARROM)
    texto_tracking(d, H-62, "BELEZA QUE VEM DA NATUREZA", mont(28,700), CREME, tracking=6)
    return img

# ---- decisao de layout (pra integrar no pipeline) ----
def escolher_layout(eh_kit, indice):
    """Kit nunca vai pro layout informativo. Produto unico alterna 1<->2."""
    if eh_kit:
        return "kit"                       # tratado por layout proprio (futuro)
    return "dramatico" if indice % 2 == 0 else "informativo"
