# -*- coding: utf-8 -*-
"""
Escolhe QUAL produto entra em cada publicacao (sem repetir) e qual TIPO de carrossel.
Indice do produto varia por dia, horario e formato (feed/story/reel/carrossel):
- feed da manha e da noite pegam produtos diferentes (horarios diferentes);
- story, reel, carrossel e feed do mesmo dia pegam produtos diferentes (deslocamento por formato).
Tipo do carrossel intercala: beneficios -> curiosidades -> modo de usar.
"""
try:
    from src import tempo
except ImportError:
    import tempo

_OFFSET = {"feed": 0, "story": 7, "reel": 13, "carrossel": 19}
_TIPOS_CARR = ["beneficios", "curiosidades", "modo_usar"]


def indice_produto(formato="feed"):
    a = tempo.agora()
    base = a.timetuple().tm_yday * 24 + a.hour
    return base + _OFFSET.get(formato, 0)


def tipo_carrossel(indice=None):
    if indice is None:
        indice = tempo.agora().timetuple().tm_yday
    return _TIPOS_CARR[indice % len(_TIPOS_CARR)]
