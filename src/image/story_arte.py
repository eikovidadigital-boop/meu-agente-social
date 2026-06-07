# -*- coding: utf-8 -*-
"""Story 9:16 (1080x1920). Frasco protagonista + folhas naturais no fundo."""
from PIL import Image, ImageDraw, ImageFilter
try:
    from src.image.arte_informativo import (VERDE, VERDE_ESC, MARROM, MARROM_ESC, CREME, BRANCO,
                                            mont, anton, quebrar, frasco_demo, FOCO_LABEL)
except ImportError:
    from image.arte_informativo import (VERDE, VERDE_ESC, MARROM, MARROM_ESC, CREME, BRANCO,
                                        mont, anton, quebrar, frasco_demo, FOCO_LABEL)
import numpy as np, math

SW, SH = 1080, 1920
TOPO_SEG, BASE_SEG = 270, 1680

def _texto_tracking(d, y, txt, font, fill, tracking=0, cx=SW//2):
    larg = sum(d.textlength(c, font=font)+tracking for c in txt)-tracking
    x = cx-larg/2
    for c in txt:
        d.text((x, y), c, font=font, fill=fill); x += d.textlength(c, font=font)+tracking

def _folha(L=170, Wmax=78, cor=(135,173,37,80)):
    img = Image.new("RGBA", (L+12, Wmax+12), (0,0,0,0)); d = ImageDraw.Draw(img)
    cy = (Wmax+12)/2; N = 44; pts = []
    for i in range(N+1):
        t=i/N; w=math.sin(math.pi*t)**0.8*Wmax/2; pts.append((6+t*L, cy-w))
    for i in range(N,-1,-1):
        t=i/N; w=math.sin(math.pi*t)**0.8*Wmax/2; pts.append((6+t*L, cy+w))
    d.polygon(pts, fill=cor)
    d.line([(6,cy),(6+L,cy)], fill=(cor[0],cor[1],cor[2],min(255,cor[3]+50)), width=2)
    return img

def _ramo(base, x0, y0, ang0, comp, n, escala, cor, curv=28):
    cau = max(cor[3]-10, 40)
    cstem = (cor[0], cor[1], cor[2], cau)
    d = ImageDraw.Draw(base)
    pts = []
    for i in range(n+1):
        t = i/n; ang = ang0 + curv*t
        x = x0 + comp*t*math.cos(math.radians(ang))
        y = y0 + comp*t*math.sin(math.radians(ang))
        pts.append((x, y, ang))
    d.line([(p[0], p[1]) for p in pts], fill=cstem, width=3)
    for i in range(1, n+1):
        x, y, ang = pts[i]
        lado = 1 if i % 2 else -1
        tam = escala * (1.0 - 0.45*(i/n))           # folhas diminuem na ponta
        f = _folha(int(150*tam), int(66*tam), cor).rotate(-(ang + 55*lado), expand=True, resample=Image.BICUBIC)
        base.alpha_composite(f, (int(x-f.size[0]/2), int(y-f.size[1]/2)))

def _halo(cx, cy, r=460):
    arr = np.zeros((SH, SW, 4), dtype=np.uint8)
    yy, xx = np.ogrid[:SH, :SW]
    dist = np.sqrt((xx-cx)**2 + (yy-cy)**2)
    a = np.clip(1 - dist/r, 0, 1)**1.6
    arr[..., 0] = 255; arr[..., 1] = 252; arr[..., 2] = 244
    arr[..., 3] = (a*150).astype(np.uint8)
    return Image.fromarray(arr, "RGBA")

def montar_story(produto_rgba, nome, foco, tagline3, cta="ACESSE O LINK NA BIO", selo="PRODUTO DO DIA"):
    img = Image.new("RGB", (SW, SH), CREME)
    noise = (np.random.rand(SH, SW, 1)*8).astype(np.uint8)
    img = Image.fromarray(np.clip(np.array(img).astype(np.int16)-4+noise, 0, 255).astype(np.uint8), "RGB").convert("RGBA")

    # --- folhas no fundo (ramos entrando pelos cantos) ---
    folhas = Image.new("RGBA", (SW, SH), (0,0,0,0))
    _ramo(folhas, -30, -30, 38, 430, 5, 1.1, (135,173,37,80))        # topo-esq
    _ramo(folhas, SW+30, -20, 148, 360, 4, 0.95, (104,134,24,70))    # topo-dir
    _ramo(folhas, SW+30, SH+30, 212, 470, 6, 1.15, (135,173,37,80))  # base-dir
    _ramo(folhas, -30, SH+20, -38, 400, 5, 1.0, (104,134,24,70))     # base-esq
    img.alpha_composite(folhas.filter(ImageFilter.GaussianBlur(1.5)))

    # --- halo atras do frasco ---
    img.alpha_composite(_halo(SW//2, 1020, 500))
    d = ImageDraw.Draw(img); cx = SW//2

    # selo topo
    sf = mont(30,800); sw_ = d.textlength(selo, font=sf)+64
    d.rounded_rectangle([cx-sw_//2, TOPO_SEG, cx+sw_//2, TOPO_SEG+62], radius=31, fill=VERDE)
    d.text((cx, TOPO_SEG+31), selo, font=sf, fill=BRANCO, anchor="mm")
    # titulo
    y = TOPO_SEG+96
    d.text((cx, y), "ÓLEO DE", font=mont(32,700), fill=VERDE_ESC, anchor="ma"); y += 48
    fn = anton(108); asc = fn.getbbox("AÇ")[3]
    for ln in quebrar(d, nome.upper(), fn, SW-120):
        d.text((cx, y), ln, font=fn, fill=MARROM_ESC, anchor="ma"); y += asc+12
    d.text((cx, y+6), "  •  ".join(t.upper() for t in tagline3), font=mont(30,700), fill=VERDE, anchor="ma"); y += 56
    flab = FOCO_LABEL.get(foco, "")
    if flab:
        ff = mont(24,800); fw = d.textlength(flab, font=ff)+44
        d.rounded_rectangle([cx-fw//2, y, cx+fw//2, y+48], radius=24, fill=MARROM)
        d.text((cx, y+24), flab, font=ff, fill=BRANCO, anchor="mm")

    # frasco PROTAGONISTA (maior)
    pr = produto_rgba.copy()
    max_h, max_w = 740, 600
    e = min(max_w/pr.size[0], max_h/pr.size[1])
    pr = pr.resize((int(pr.size[0]*e), int(pr.size[1]*e)), Image.LANCZOS)
    fx = cx - pr.size[0]//2; fy = 640
    sh = Image.new("RGBA",(SW,SH),(0,0,0,0)); sd=ImageDraw.Draw(sh)
    sd.ellipse([fx+pr.size[0]*0.08, fy+pr.size[1]-44, fx+pr.size[0]*0.92, fy+pr.size[1]+40], fill=(60,40,30,130))
    img.alpha_composite(sh.filter(ImageFilter.GaussianBlur(26)))
    img.alpha_composite(pr.convert("RGBA"), (fx, fy))
    d = ImageDraw.Draw(img)

    # CTA -> sempre direciona para a BIO (sem link, sem figurinha)
    cy2 = BASE_SEG-205
    _texto_tracking(d, cy2, "100% PURO E NATURAL • PRENSADO A FRIO", mont(24,700), VERDE_ESC, tracking=2)
    bw, bh = 600, 96; bx = cx-bw//2; byy = cy2+50
    d.rounded_rectangle([bx, byy, bx+bw, byy+bh], radius=bh//2, fill=MARROM)
    # seta para cima (a bio fica no topo do perfil) + texto, fonte ajustada pra caber
    fsz = 32
    while d.textlength(cta, font=mont(fsz, 800)) > bw-90 and fsz > 20:
        fsz -= 1
    fb = mont(fsz, 800)
    tw = d.textlength(cta, font=fb); ax = cx - tw/2 - 34; ay = byy + bh/2
    d.polygon([(ax, ay+10), (ax+24, ay+10), (ax+12, ay-12)], fill=CREME)   # triangulo p/ cima
    d.text((cx+18, ay), cta, font=fb, fill=CREME, anchor="mm")
    return img.convert("RGB")

if __name__ == "__main__":
    art = montar_story(frasco_demo("120 ml"), "Rosa Mosqueta", "PELE", ["Regenera","Ilumina","Renova"])
    art.save("mockup_story.png"); print("ok", art.size)
