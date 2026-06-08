# -*- coding: utf-8 -*-
"""
Gerador de FUNDO por IA pro story/reel. Intercala 4 climas (suave, ingredientes,
rustico, minimalista) a cada publicacao. Os prompts pedem fundo VERTICAL, sem texto
e sem produto (o frasco real e o texto entram por cima), com espaco pro conteudo.
"""
import base64
import os
from io import BytesIO

import requests
from PIL import Image

ESTILOS = ["suave", "ingredientes", "rustico", "minimalista"]

_PROMPTS = {
    "suave": (
        "Vertical 9:16 background for a premium natural cosmetics brand. Soft tropical "
        "green leaves and delicate botanical foliage, gently blurred with shallow depth "
        "of field, warm diffused morning sunlight, airy and serene, generous soft empty "
        "space in the upper and central area. Palette of cream, sage green and warm brown. "
        "Editorial premium photography, dreamy natural bokeh, elegant and clean. "
        "No text, no labels, no bottles, no products, no people."
    ),
    "ingredientes": (
        "Vertical 9:16 background for a premium natural oil brand inspired by {ing}. "
        "Fresh {ing} and natural botanical elements softly blurred in the background, "
        "scattered seeds, nuts, leaves and glossy droplets of golden oil, warm natural "
        "light, organic and inviting, generous soft empty space in the upper area. "
        "Cream and warm earthy tones. Editorial product photography, elegant shallow "
        "depth of field. No text, no labels, no bottles, no products, no people."
    ),
    "rustico": (
        "Vertical 9:16 cozy rustic background for a natural cosmetics brand: weathered "
        "light wood surface, soft natural linen cloth, smooth river stones and a few fresh "
        "green botanical sprigs, warm spa-like ambient light, calm and inviting, generous "
        "soft empty space in the center and top. Palette of cream, beige, sage and warm "
        "brown, gentle soft shadows. Premium lifestyle photography, soft depth of field. "
        "No text, no labels, no bottles, no products, no people."
    ),
    "minimalista": (
        "Vertical 9:16 clean minimalist background for a premium natural brand: smooth soft "
        "gradient of cream and pale sage green, very subtle paper-like organic texture, one "
        "softly blurred leaf shadow gently falling in a corner, lots of negative space, calm "
        "and sophisticated. Soft studio lighting, ultra clean and elegant. "
        "No text, no labels, no bottles, no products, no people."
    ),
}


def escolher_estilo(indice):
    return ESTILOS[indice % len(ESTILOS)]


def prompt_fundo(indice, ingrediente=""):
    """Devolve (prompt, estilo) do dia, intercalando os 4 climas."""
    estilo = escolher_estilo(indice)
    ing = (ingrediente or "natural botanicals").strip()
    return _PROMPTS[estilo].format(ing=ing), estilo


def gerar_fundo_ia(prompt, size="1024x1792", timeout=120):
    """Gera o fundo via OpenAI (retrato) e devolve um PIL.Image. Lanca em caso de erro."""
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        raise RuntimeError("OPENAI_API_KEY ausente")
    r = requests.post(
        "https://api.openai.com/v1/images/generations",
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        json={"model": "dall-e-3", "prompt": prompt, "size": size,
              "response_format": "b64_json", "n": 1},
        timeout=timeout,
    ).json()
    if "data" not in r:
        raise RuntimeError(f"Geracao do fundo falhou: {r.get('error', r)}")
    b64 = r["data"][0]["b64_json"]
    return Image.open(BytesIO(base64.b64decode(b64))).convert("RGB")


def fundo_do_dia(indice, ingrediente=""):
    """Conveniencia: gera o fundo do dia (com o estilo rotativo). None se falhar."""
    try:
        prompt, estilo = prompt_fundo(indice, ingrediente)
        img = gerar_fundo_ia(prompt)
        print(f"Fundo de IA gerado | estilo: {estilo}")
        return img
    except Exception as e:
        print("aviso: fundo de IA falhou, usando fundo desenhado:", e)
        return None
