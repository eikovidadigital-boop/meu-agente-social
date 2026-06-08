# -*- coding: utf-8 -*-
"""Registra cada publicacao em HISTORICO_POSTS.md (tabela markdown, pronta pro Obsidian)."""
import os
from datetime import datetime

ARQ = os.environ.get("HISTORICO_ARQ", "HISTORICO_POSTS.md")


def registrar(tipo, produto, media_id="", obs=""):
    novo = not os.path.exists(ARQ)
    try:
        with open(ARQ, "a", encoding="utf-8") as f:
            if novo:
                f.write("# Histórico de publicações — EikoVida\n\n")
                f.write("| Data | Tipo | Produto | ID | Obs |\n|---|---|---|---|---|\n")
            data = datetime.now().strftime("%d/%m/%Y %H:%M")
            f.write(f"| {data} | {tipo} | {produto} | {media_id} | {obs} |\n")
    except Exception as e:
        print("aviso: nao consegui gravar o historico:", e)
