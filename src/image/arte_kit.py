# -*- coding: utf-8 -*-
"""Layout 3 — KIT (varios frascos). Visual de 'combo/presente', centralizado."""
from PIL import Image, ImageDraw, ImageFilter
try:
    from src.image.arte_informativo import (W, H, VERDE, VERDE_ESC, MARROM, MARROM_ESC, CREME, BRANCO,
                                            mont, anton, quebrar, desenhar_check, frasco_demo, texto_tracking)
except ImportError:
    from image.arte_informativo import (W, H, VERDE, VERDE_ESC, MARROM, MARROM_ESC, CREME, BRANCO,
                                        mont, anton, quebrar, desenhar_check, frasco_demo, texto_tracking)
import numpy as np

def _fundo():
    img = Image.new("RGB", (W, H), CREME)
    noise = (np.random.rand(H, W, 1)*8).astype(np.uint8)
    return Image.fromarray(np.clip(np.array(img).astype(np.int16)-4+noise, 0, 255).astype(np.uint8), "RGB")

def montar_kit(produtos_rgba, nome, itens, tagline3, descricao, volume_label="KIT"):
    if len(produtos_rgba) < 2:
        raise ValueError("Kit precisa de 2+ produtos. Produto unico usa layout 1 ou 2.")
    img = _fundo(); d = ImageDraw.Draw(img)

    # faixa topo
    d.rectangle([0,0,W,70], fill=VERDE)
    texto_tracking(d, 22, "100% PURO E NATURAL  •  PRENSADO A FRIO", mont(24,700), BRANCO, tracking=4)

    # badge KIT central
    bf = mont(26,800); btxt = f"KIT COM {len(produtos_rgba)} ÓLEOS"
    bw = d.textlength(btxt, font=bf)+56
    d.rounded_rectangle([(W-bw)//2,104,(W+bw)//2,160], radius=28, fill=MARROM)
    d.text((W//2,132), btxt, font=bf, fill=CREME, anchor="mm")

    # titulo centralizado
    fn = anton(82); asc = fn.getbbox("AÇ")[3]; y=190
    for ln in quebrar(d, nome.upper(), fn, W-140):
        d.text((W//2, y), ln, font=fn, fill=MARROM_ESC, anchor="ma"); y += asc+10
    # tagline
    d.text((W//2, y+6), "  •  ".join(t.upper() for t in tagline3), font=mont(26,700), fill=VERDE, anchor="ma"); y += 56

    # vitrine (painel arredondado) atras dos frascos
    vit_t, vit_b = y+24, 1010
    d.rounded_rectangle([70, vit_t, W-70, vit_b], radius=40, fill=(236,228,208))
    d.rounded_rectangle([70, vit_t, W-70, vit_t+10], radius=40, fill=VERDE)

    # frascos lado a lado, leve sobreposicao, do meio a frente
    n = len(produtos_rgba); base = vit_b - 40
    alvo_h = 470 if n <= 3 else 400
    escalados = []
    for p in produtos_rgba:
        e = alvo_h/p.size[1]; escalados.append(p.resize((int(p.size[0]*e), int(p.size[1]*e)), Image.LANCZOS))
    larg_total = sum(s.size[0] for s in escalados) - int(0.30*sum(s.size[0] for s in escalados[1:]))
    x = (W - larg_total)//2
    ordem = sorted(range(n), key=lambda i: abs(i-(n-1)/2), reverse=True)  # meio por ultimo
    posicoes = []
    for s in escalados:
        posicoes.append(x); x += int(s.size[0]*0.70)
    for i in ordem:
        s = escalados[i]; px = posicoes[i]; py = base - s.size[1]
        boost = 1.06 if i == n//2 else 1.0
        if boost != 1.0:
            s = s.resize((int(s.size[0]*boost), int(s.size[1]*boost)), Image.LANCZOS); py = base - s.size[1]
        sh = Image.new("RGBA",(W,H),(0,0,0,0)); sd=ImageDraw.Draw(sh)
        sd.ellipse([px+10, base-25, px+s.size[0]-10, base+22], fill=(60,40,30,110))
        img.paste(Image.new("RGB",(W,H),(0,0,0)), (0,0), sh.filter(ImageFilter.GaussianBlur(16)).split()[3])
        img.paste(s, (px, py), s)
    d = ImageDraw.Draw(img)

    # descricao curta (1 linha) abaixo da vitrine
    fdesc = mont(25,500); dy = vit_b+24
    for ln in quebrar(d, descricao, fdesc, W-160)[:2]:
        d.text((W//2, dy), ln, font=fdesc, fill=(80,66,60), anchor="ma"); dy += 34

    # lista de itens (nomes dos oleos) em 2 colunas com check
    dy += 12; fb = mont(25,700); col_x = [140, W//2+30]
    for idx, it in enumerate(itens[:6]):
        cx = col_x[idx % 2]; ry = dy + (idx//2)*46
        desenhar_check(d, cx, ry+13, 14)
        d.text((cx+30, ry), it, font=fb, fill=MARROM_ESC)

    # rodape
    d.rectangle([0,H-90,W,H], fill=MARROM)
    texto_tracking(d, H-62, "BELEZA QUE VEM DA NATUREZA", mont(28,700), CREME, tracking=6)
    return img

if __name__ == "__main__":
    frascos = [frasco_demo("120 ml"), frasco_demo("120 ml"), frasco_demo("120 ml")]
    art = montar_kit(frascos, nome="Kit Cuidado Capilar",
                     itens=["Óleo de Coco","Óleo de Rícino","Óleo de Alecrim"],
                     tagline3=["Nutre","Fortalece","Brilho"],
                     descricao="Três óleos 100% puros para o ritual completo de cuidado dos fios.")
    art.save("mockup_kit.png"); print("ok", art.size)
