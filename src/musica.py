# -*- coding: utf-8 -*-
"""Escolhe a trilha do Reel, intercalando os arquivos da pasta audio/ (rotaciona por dia)."""
import glob
import os

def pasta_audio():
    return os.path.join(os.path.dirname(__file__), "..", "audio")

def escolher_musica(indice):
    arqs = sorted(glob.glob(os.path.join(pasta_audio(), "*.mp3")))
    return arqs[indice % len(arqs)] if arqs else None
