# -*- coding: utf-8 -*-
"""
run_comentarios.py — Atendimento automático nos comentários do Instagram.

Roda pelo GitHub Actions a cada 15 min:
1. Descobre a conta do Instagram pelo token.
2. Lê os comentários dos posts recentes.
3. Ignora: já respondidos, da própria conta, e mais antigos que JANELA_HORAS.
4. Gera resposta com IA (simpática + compliance) e escolhe o produto.
5. Responde o comentário; em dúvida de compra, cola o link direto do produto.
6. Marca como respondido (estado commitado pelo workflow).
"""
import os
import sys
from datetime import datetime, timezone, timedelta

# garante que "src" seja importável rodando da raiz do repo
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.comentarios import (
    instagram_comentarios as ig,
    produtos_lite,
    resposta_ia,
    estado,
)
from src.comentarios.resposta_ia import bloco_contato

# ---- Configurações de segurança ----
JANELA_HORAS = 48          # não responde comentários mais antigos que isso
MAX_POSTS = 20             # quantos posts recentes varrer
MAX_RESPOSTAS_POR_RUN = 20 # teto de respostas por execução (evita disparo em massa)


def _recente(timestamp_iso: str) -> bool:
    """True se o comentário é das últimas JANELA_HORAS."""
    if not timestamp_iso:
        return True
    try:
        # formato da Graph API: 2026-06-17T12:34:56+0000
        ts = datetime.strptime(timestamp_iso, "%Y-%m-%dT%H:%M:%S%z")
    except Exception:
        return True
    return (datetime.now(timezone.utc) - ts) <= timedelta(hours=JANELA_HORAS)


def main():
    token = os.environ.get("PAGE_ACCESS_TOKEN")
    if not token:
        print("ERRO: secret PAGE_ACCESS_TOKEN não configurado.")
        return
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("ERRO: secret ANTHROPIC_API_KEY não configurado.")
        return

    ig_user_id = os.environ.get("IG_USER_ID") or ig.descobrir_ig_user_id(token)
    if not ig_user_id:
        print("ERRO: não consegui descobrir o IG User ID pela página.")
        return
    print(f"[ok] conta Instagram: {ig_user_id}")

    eu = ig.meu_username(ig_user_id, token)
    respondidos = estado.carregar()
    produtos = produtos_lite.carregar_produtos()
    catalogo = produtos_lite.montar_contexto(produtos)

    posts = ig.listar_posts_recentes(ig_user_id, token, MAX_POSTS)
    print(f"[ok] {len(posts)} posts recentes para varrer.")

    enviadas = 0
    for post in posts:
        if enviadas >= MAX_RESPOSTAS_POR_RUN:
            print("[limite] teto de respostas por execução atingido.")
            break

        legenda = post.get("caption", "")
        comentarios = ig.listar_comentarios(post["id"], token)

        for c in comentarios:
            cid = c.get("id")
            autor = (c.get("username") or "").lower()
            texto = c.get("text", "")

            if not cid or cid in respondidos:
                continue
            if autor and eu and autor == eu:      # não responde a si mesmo
                continue
            if not _recente(c.get("timestamp")):   # comentário antigo, ignora
                estado.marcar(cid)                 # marca pra não reavaliar sempre
                continue
            if not texto.strip():
                estado.marcar(cid)
                continue

            resultado = resposta_ia.gerar(texto, legenda, catalogo)
            tipo = resultado["tipo"]
            resposta = resultado["resposta"]
            link = resultado["produto_link"]
            anexar = resultado["anexar"]

            if tipo == "IGNORAR" or not resposta:
                estado.marcar(cid)
                print(f"  - @{autor}: ignorado (spam/sem sentido ou sem resposta segura).")
                continue

            mensagem = resposta
            if anexar == "LINK" and link:
                mensagem = f"{resposta}\n\n👉 {link}"
            elif anexar == "CONTATO":
                mensagem = f"{resposta}\n\n{bloco_contato()}"

            if ig.responder_comentario(cid, mensagem, token):
                estado.marcar(cid)
                enviadas += 1
                print(f"  ✓ @{autor} [{tipo}] respondido.")
            else:
                print(f"  ✗ @{autor}: falha ao publicar resposta.")

    print(f"\n[fim] {enviadas} respostas publicadas nesta execução.")


if __name__ == "__main__":
    main()
