# -*- coding: utf-8 -*-
"""
Arte dos CARROSSEIS (1080x1350). Tres tipos que o sistema intercala:
beneficios, modo_usar, curiosidades. Todos os slides com a mesma identidade
(faixa de marca, cores, fontes), pra ficar coeso e profissional.
O Instagram corta os slides pela proporcao do 1o, entao todos sao 1080x1350.
"""
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

try:
    from src.image.arte_informativo import (VERDE, VERDE_ESC, MARROM, MARROM_ESC,
                                            CREME, BRANCO, mont, anton, quebrar, frasco_demo)
except ImportError:
    from image.arte_informativo import (VERDE, VERDE_ESC, MARROM, MARROM_ESC,
                                        CREME, BRANCO, mont, anton, quebrar, frasco_demo)

W, H = 1080, 1350

TIPOS = {
    "beneficios":   {"badge": "BENEFÍCIOS",    "titulo": "BENEFÍCIOS DO",  "sub": "Arraste e descubra"},
    "modo_usar":    {"badge": "MODO DE USAR",  "titulo": "COMO USAR O",    "sub": "Passo a passo"},
    "curiosidades": {"badge": "VOCÊ SABIA?",   "titulo": "CURIOSIDADES DO","sub": "Você vai se surpreender"},
}


def _base():
    img = Image.new("RGB", (W, H), CREME)
    noise = (np.random.rand(H, W, 1) * 7).astype(np.uint8)
    img = Image.fromarray(np.clip(np.array(img).astype(np.int16) - 3 + noise, 0, 255).astype(np.uint8), "RGB")
    return img.convert("RGBA")


def _marca_topo(d):
    d.rectangle([0, 0, W, 76], fill=VERDE)
    d.text((W // 2, 38), "EIKO VIDA  •  100% NATURAL", font=mont(26, 800), fill=BRANCO, anchor="mm")


def _rodape(d, prog=None):
    d.rectangle([0, H - 66, W, H], fill=MARROM)
    txt = prog if prog else "BELEZA QUE VEM DA NATUREZA"
    d.text((W // 2, H - 33), txt, font=mont(24, 700), fill=CREME, anchor="mm")


def _arraste(d):
    d.text((W - 70, H - 120), "→", font=anton(56), fill=VERDE_ESC, anchor="mm")
    d.text((W - 205, H - 120), "ARRASTE", font=mont(24, 800), fill=MARROM, anchor="mm")


def _frasco(img, frasco, maxh, cy_top):
    fr = frasco.copy()
    e = maxh / fr.size[1]
    fr = fr.resize((max(1, int(fr.size[0] * e)), max(1, int(fr.size[1] * e))), Image.LANCZOS)
    img.alpha_composite(fr, (W // 2 - fr.size[0] // 2, cy_top))


def slide_capa(tipo, nome, frasco):
    cfg = TIPOS[tipo]
    img = _base(); d = ImageDraw.Draw(img); cx = W // 2
    _marca_topo(d)
    # badge do tipo
    f = mont(28, 800); tw = d.textlength(cfg["badge"], font=f); bw = tw + 64; bx = cx - bw / 2; by = 150
    d.rounded_rectangle([bx, by, bx + bw, by + 58], radius=29, fill=VERDE)
    d.text((cx, by + 29), cfg["badge"], font=f, fill=BRANCO, anchor="mm")
    # titulo
    d.text((cx, 252), cfg["titulo"], font=mont(38, 800), fill=VERDE_ESC, anchor="mm")
    fn = anton(112); nome_up = nome.upper()
    while d.textlength(nome_up, font=fn) > W - 90 and fn.size > 58:
        fn = anton(fn.size - 4)
    d.text((cx, 340), nome_up, font=fn, fill=MARROM_ESC, anchor="mm")
    d.text((cx, 432), cfg["sub"], font=mont(30, 600), fill=MARROM, anchor="mm")
    _frasco(img, frasco, 600, H - 600 - 110); d = ImageDraw.Draw(img)
    _arraste(d); _rodape(d)
    return img.convert("RGB")


def slide_item(numero, total, titulo, texto, tipo):
    img = _base(); d = ImageDraw.Draw(img)
    _marca_topo(d)
    # numero em circulo
    nx, ny = 150, 210
    d.ellipse([nx - 72, ny - 72, nx + 72, ny + 72], fill=VERDE)
    d.text((nx, ny), f"{numero:02d}", font=anton(66), fill=BRANCO, anchor="mm")
    # titulo do item (ao lado do numero)
    fn = anton(54); ty = 162
    for ln in quebrar(d, titulo.upper(), fn, W - 290):
        d.text((258, ty), ln, font=fn, fill=MARROM_ESC); ty += 60
    # card central com sombra contendo o texto
    m = 70; card_top = 440; card_h = 540
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0)); sd = ImageDraw.Draw(sh)
    sd.rounded_rectangle([m + 8, card_top + 12, W - m + 8, card_top + card_h + 12], radius=38, fill=(60, 40, 30, 70))
    img.alpha_composite(sh.filter(ImageFilter.GaussianBlur(14))); d = ImageDraw.Draw(img)
    d.rounded_rectangle([m, card_top, W - m, card_top + card_h], radius=38, fill=BRANCO)
    d.rounded_rectangle([m, card_top, W - m, card_top + 16], radius=8, fill=VERDE)
    # texto centralizado verticalmente no card
    ft = mont(42, 500); linhas = quebrar(d, texto, ft, W - 2 * m - 90)
    th = len(linhas) * 60; sy = card_top + (card_h - th) // 2 + 10
    for ln in linhas:
        d.text((W // 2, sy), ln, font=ft, fill=(58, 46, 40), anchor="ma"); sy += 60
    _arraste(d); _rodape(d, f"{numero} de {total}")
    return img.convert("RGB")


def slide_cta(nome, frasco):
    img = _base(); d = ImageDraw.Draw(img); cx = W // 2
    _marca_topo(d)
    d.text((cx, 180), "GOSTOU?", font=anton(74), fill=MARROM_ESC, anchor="mm")
    d.text((cx, 256), f"Garanta o seu Óleo de {nome}", font=mont(32, 600), fill=MARROM, anchor="mm")
    _frasco(img, frasco, 540, 300); d = ImageDraw.Draw(img)
    bw = 640; bx = cx - bw / 2; byy = H - 205
    d.rounded_rectangle([bx, byy, bx + bw, byy + 94], radius=47, fill=MARROM)
    d.text((cx, byy + 47), "TOQUE PARA COMPRAR", font=mont(36, 800), fill=CREME, anchor="mm")
    return img.convert("RGB")


def montar_carrossel(tipo, nome, frasco, itens):
    """itens = lista de (titulo, texto). Devolve a lista de slides (PIL)."""
    slides = [slide_capa(tipo, nome, frasco)]
    for i, (t, txt) in enumerate(itens, 1):
        slides.append(slide_item(i, len(itens), t, txt, tipo))
    slides.append(slide_cta(nome, frasco))
    return slides
