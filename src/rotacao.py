# -*- coding: utf-8 -*-
"""
Escolhe QUAL produto entra em cada publicacao, sem repetir.
O indice varia por dia, por horario e por formato (feed/story/reel), entao:
- o feed da manha e o da noite pegam produtos diferentes (horarios diferentes);
- story, reel e feed do mesmo dia pegam produtos diferentes (deslocamento por formato).
"""
from datetime import datetime

_OFFSET = {"feed": 0, "story": 7, "reel": 13}

def indice_produto(formato="feed"):
    a = datetime.now()
    base = a.timetuple().tm_yday * 24 + a.hour
    return base + _OFFSET.get(formato, 0)
