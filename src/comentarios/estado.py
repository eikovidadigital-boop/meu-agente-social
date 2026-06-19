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
    ids = []
    if os.path.exists(ARQUIVO):
        with open(ARQUIVO, "r", encoding="utf-8") as f:
            ids = [l.strip() for l in f if l.strip()]
    if comment_id in ids:
        return
    ids.append(comment_id)
    # Mantem so os ultimos 3000 IDs. A janela de resposta e de 48h, entao 3000
    # comentarios e folga de sobra — e o arquivo para de crescer pra sempre.
    ids = ids[-3000:]
    with open(ARQUIVO, "w", encoding="utf-8") as f:
        f.write("\n".join(ids) + "\n")
