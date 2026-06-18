# -*- coding: utf-8 -*-
"""
Estado do agente de Direct: guarda os IDs das mensagens ja respondidas,
pra nunca responder a mesma DM duas vezes. O workflow faz commit do arquivo.
"""
import os

ARQUIVO = "data/direct_respondidos.txt"


def carregar():
    if not os.path.exists(ARQUIVO):
        return set()
    with open(ARQUIVO, "r", encoding="utf-8") as f:
        return set(l.strip() for l in f if l.strip())


def marcar(msg_id):
    os.makedirs(os.path.dirname(ARQUIVO), exist_ok=True)
    with open(ARQUIVO, "a", encoding="utf-8") as f:
        f.write(str(msg_id) + "\n")
