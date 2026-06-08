# -*- coding: utf-8 -*-
"""
Legenda persuasiva pro Reel: gancho + beneficio cosmetico + diferencial + CTA de compra.
Varia por foco e por dia (nao repete). Linguagem cosmetica (sem claim de cura/ANVISA).
"""
from src.compliance import garantir

_GANCHO = {
    "PELE": [
        "Sua pele merece o que a natureza tem de melhor.",
        "Aquele viço natural que todo mundo nota.",
        "Hidratação de verdade não vem de fórmula — vem da natureza.",
        "A rotina de pele mais pura que você vai experimentar.",
    ],
    "CABELO": [
        "Seus fios pedindo um cuidado de verdade.",
        "Cabelo macio, nutrido e com brilho natural.",
        "O segredo natural pra fios mais bonitos.",
        "Nutrição que seus cabelos vão sentir.",
    ],
    "SAUDE": [
        "Puro como a natureza fez — pro seu dia a dia.",
        "O melhor da natureza, sem química nenhuma.",
        "Qualidade natural que você leva pra casa.",
        "Do jeito que a natureza entrega: 100% puro.",
    ],
}
_GENERICO = _GANCHO["SAUDE"]

_BENEF = {
    "PELE": "Nutre, hidrata e realça o viço natural da pele.",
    "CABELO": "Ajuda a nutrir os fios, deixando o cabelo macio e com brilho.",
    "SAUDE": "Óleo vegetal puro, extraído com cuidado pra manter tudo o que a natureza oferece.",
}
_HASHTAG = {
    "PELE": "#eikovida #oleosnaturais #peleperfeita #skincarenatural #cuidadonatural #belezanatural",
    "CABELO": "#eikovida #oleosnaturais #cabelosnaturais #cuidadocapilar #belezanatural #cronogramacapilar",
    "SAUDE": "#eikovida #oleosnaturais #cosmeticosnaturais #vidanatural #produtonatural #belezanatural",
}


def legenda_reel(nome, foco, tagline3=None, indice=0):
    foco = foco if foco in _GANCHO else "SAUDE"
    gancho = _GANCHO[foco][indice % len(_GANCHO[foco])]
    benef = _BENEF[foco]
    tag = _HASHTAG[foco]
    corpo = (
        f"{gancho}\n\n"
        f"✨ Óleo de {nome}\n"
        f"{benef}\n"
        f"🌿 100% puro e natural • prensado a frio\n\n"
        f"🛍️ Toque no produto marcado e garanta o seu — enviamos pra todo o Brasil!"
    )
    fallback = f"Óleo de {nome} 🌿 100% puro e natural. Toque no produto pra comprar.\n\n{tag}"
    return garantir(corpo, fallback) + "\n\n" + tag
