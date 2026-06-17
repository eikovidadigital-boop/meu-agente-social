# -*- coding: utf-8 -*-
"""
Guarda quais comentários já foram respondidos, pra nunca responder 2x.
Estado em data/comentarios_respondidos.txt (um ID por linha).
O workflow commita esse arquivo de volta ao repo a cada execução.
"""
import os

ARQUIVO = os.path.join("data", "comentarios_respondidos.txt")


def carregar():
    if not os.path.exists(ARQUIVO):
        return set()
    with open(ARQUIVO, "r", encoding="utf-8") as f:
        return set(linha.strip() for linha in f if linha.strip())


def marcar(comment_id: str):
    os.makedirs("data", exist_ok=True)
    with open(ARQUIVO, "a", encoding="utf-8") as f:
        f.write(comment_id + "\n")
