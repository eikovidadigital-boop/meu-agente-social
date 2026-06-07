# -*- coding: utf-8 -*-
"""Story 9:16 (1080x1920). Cabecalho fluido (nao sobrepoe), frasco protagonista, folhas naturais."""
try:
    from src.image.arte_informativo import (VERDE, VERDE_ESC, MARROM, MARROM_ESC, CREME, BRANCO,
                                            mont, anton, quebrar, frasco_demo, FOCO_LABEL)
except ImportError:
    from image.arte_informativo import (VERDE, VERDE_ESC, MARROM, MARROM_ESC, CREME, BRANCO,
                                        mont, anton, quebrar, frasco_demo, FOCO_LABEL)
import numpy as np, math, re
from PIL import Image, ImageDraw, ImageFilter

SW, SH = 1080, 1920
TOPO_SEG, BASE_SEG = 270, 1680


def limpar_nome(nome):
    """Tira 'Óleo de', volume, marca e termos longos -> nome curto pro titulo."""
    n = nome or ""
    n = re.sub(r'(?i)^\s*[óo]leo\s+(vegetal\s+)?(de\s+|da\s+|do\s+)?', '', n)
    n = re.sub(r'(?i)\b\d+\s*ml\b', '', n)
    n = re.sub(r'(?i)\beiko\s*vida\b|\beiko\b', '', n)
    n = re.sub(r'(?i)\bn[ãa]o\s+refinad[oa]\b', '', n)
    n = re.sub(r'(?i)\bprensad[oa]\s+a\s+frio\b', '', n)
    n = re.sub(r'\s{2,}', ' ', n).strip(' -•,')
    return n or (nome or "").strip()


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
    d.polygon(pts, fill=cor); d.line([(6,cy),(6+L,cy)], fill=(cor[0],cor[1],cor[2],min(255,cor[3]+50)), width=2)
    return img


def _ramo(base, x0, y0, ang0, comp, n, escala, cor, curv=28):
    cstem = (cor[0], cor[1], cor[2], max(cor[3]-10, 40))
    d = ImageDraw.Draw(base); pts = []
    for i in range(n+1):
        t = i/n; ang = ang0 + curv*t
        pts.append((x0 + comp*t*math.cos(math.radians(ang)), y0 + comp*t*math.sin(math.radians(ang)), ang))
    d.line([(p[0], p[1]) for p in pts], fill=cstem, width=3)
    for i in range(1, n+1):
        x, y, ang = pts[i]; lado = 1 if i % 2 else -1; tam = escala*(1.0-0.45*(i/n))
        f = _folha(int(150*tam), int(66*tam), cor).rotate(-(ang+55*lado), expand=True, resample=Image.BICUBIC)
        base.alpha_composite(f, (int(x-f.size[0]/2), int(y-f.size[1]/2)))


def _halo(cx, cy, r=460):
    arr = np.zeros((SH, SW, 4), dtype=np.uint8)
    yy, xx = np.ogrid[:SH, :SW]
    a = np.clip(1 - np.sqrt((xx-cx)**2+(yy-cy)**2)/r, 0, 1)**1.6
    arr[...,0]=255; arr[...,1]=252; arr[...,2]=244; arr[...,3]=(a*150).astype(np.uint8)
    return Image.fromarray(arr, "RGBA")


def montar_story(produto_rgba, nome, foco, tagline3, cta="ACESSE O LINK NA BIO", selo="PRODUTO DO DIA"):
    nome = limpar_nome(nome)
    img = Image.new("RGB", (SW, SH), CREME)
    noise = (np.random.rand(SH, SW, 1)*8).astype(np.uint8)
    img = Image.fromarray(np.clip(np.array(img).astype(np.int16)-4+noise, 0, 255).astype(np.uint8), "RGB").convert("RGBA")

    folhas = Image.new("RGBA", (SW, SH), (0,0,0,0))
    _ramo(folhas, -30, -30, 38, 430, 5, 1.1, (135,173,37,80))
    _ramo(folhas, SW+30, -20, 148, 360, 4, 0.95, (104,134,24,70))
    _ramo(folhas, SW+30, SH+30, 212, 470, 6, 1.15, (135,173,37,80))
    _ramo(folhas, -30, SH+20, -38, 400, 5, 1.0, (104,134,24,70))
    img.alpha_composite(folhas.filter(ImageFilter.GaussianBlur(1.5)))
    d = ImageDraw.Draw(img); cx = SW//2

    # ---- CABECALHO (fluido, de cima pra baixo) ----
    y = TOPO_SEG
    sf = mont(30,800); sw_ = d.textlength(selo, font=sf)+64
    d.rounded_rectangle([cx-sw_//2, y, cx+sw_//2, y+62], radius=31, fill=VERDE)
    d.text((cx, y+31), selo, font=sf, fill=BRANCO, anchor="mm"); y += 92

    d.text((cx, y), "ÓLEO DE", font=mont(30,700), fill=VERDE_ESC, anchor="ma"); y += 46

    # titulo: fonte se ajusta para caber em no maximo 2 linhas
    size = 104
    fn = anton(size); linhas = quebrar(d, nome.upper(), fn, SW-130)
    while len(linhas) > 2 and size > 54:
        size -= 6; fn = anton(size); linhas = quebrar(d, nome.upper(), fn, SW-130)
    asc = fn.getbbox("AÇ")[3]
    for ln in linhas:
        d.text((cx, y), ln, font=fn, fill=MARROM_ESC, anchor="ma"); y += asc + 8
    y += 8

    d.text((cx, y), "  •  ".join(t.upper() for t in tagline3), font=mont(28,700), fill=VERDE, anchor="ma"); y += 52
    flab = FOCO_LABEL.get(foco, "")
    if flab:
        ff = mont(24,800); fw = d.textlength(flab, font=ff)+44
        d.rounded_rectangle([cx-fw//2, y, cx+fw//2, y+48], radius=24, fill=MARROM)
        d.text((cx, y+24), flab, font=ff, fill=BRANCO, anchor="mm"); y += 60

    # ---- FRASCO no espaco restante (entre cabecalho e CTA) ----
    cta_top = BASE_SEG - 205
    topo_frasco = y + 24
    espaco = max(360, cta_top - 30 - topo_frasco)
    pr = produto_rgba.copy()
    max_h, max_w = min(espaco, 760), 600
    e = min(max_w/pr.size[0], max_h/pr.size[1])
    pr = pr.resize((max(1,int(pr.size[0]*e)), max(1,int(pr.size[1]*e))), Image.LANCZOS)
    fx = cx - pr.size[0]//2
    fy = topo_frasco + (espaco - pr.size[1])//2
    img.alpha_composite(_halo(cx, fy + pr.size[1]//2, 470))
    sh = Image.new("RGBA",(SW,SH),(0,0,0,0)); sd=ImageDraw.Draw(sh)
    sd.ellipse([fx+pr.size[0]*0.08, fy+pr.size[1]-44, fx+pr.size[0]*0.92, fy+pr.size[1]+40], fill=(60,40,30,130))
    img.alpha_composite(sh.filter(ImageFilter.GaussianBlur(26)))
    img.alpha_composite(pr.convert("RGBA"), (fx, fy))
    d = ImageDraw.Draw(img)

    # ---- CTA -> bio ----
    _texto_tracking(d, cta_top, "100% PURO E NATURAL • PRENSADO A FRIO", mont(24,700), VERDE_ESC, tracking=2)
    bw, bh = 600, 96; bx = cx-bw//2; byy = cta_top+50
    d.rounded_rectangle([bx, byy, bx+bw, byy+bh], radius=bh//2, fill=MARROM)
    fsz = 32
    while d.textlength(cta, font=mont(fsz,800)) > bw-90 and fsz > 20: fsz -= 1
    fb = mont(fsz,800); tw = d.textlength(cta, font=fb); ax = cx - tw/2 - 34; ay = byy + bh/2
    d.polygon([(ax, ay+10),(ax+24, ay+10),(ax+12, ay-12)], fill=CREME)
    d.text((cx+18, ay), cta, font=fb, fill=CREME, anchor="mm")
    return img.convert("RGB")


if __name__ == "__main__":
    # testa com o nome poluido real do Shopify
    art = montar_story(frasco_demo("120 ml"), "Óleo de Limão Extra Virgem 120ml Eiko", "PELE",
                       ["Nutre","Refresca","Cuida"])
    art.save("mockup_story.png"); print("ok", art.size)
