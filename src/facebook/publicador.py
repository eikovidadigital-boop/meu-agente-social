# -*- coding: utf-8 -*-
"""
Modulo de publicacao no Facebook (EikoVida).

Espelha posts de FOTO UNICA e CARROSSEL na Pagina do Facebook usando o
MESMO PAGE_ACCESS_TOKEN do Instagram (agora com a permissao pages_manage_posts).

Nao precisa de secret novo. O ID da Pagina e descoberto sozinho pelo token.

Uso:
    from src.facebook.publicador import publicar_no_facebook

    # foto unica:
    publicar_no_facebook("https://.../imagem.jpg", "Minha legenda", token=config.PAGE_ACCESS_TOKEN)

    # carrossel (varias fotos no mesmo post):
    publicar_no_facebook(["https://.../1.jpg", "https://.../2.jpg"], "Legenda", token=config.PAGE_ACCESS_TOKEN)

    # se token nao for passado, ele le do ambiente (os.environ["PAGE_ACCESS_TOKEN"]).
"""

import os
import json
import httpx

# Mesma versao usada no resto do sistema (run_diario / run_carrossel).
GRAPH = "https://graph.facebook.com/v25.0"

TIMEOUT = 60.0


def _token(token=None):
    tok = (token or "").strip() or os.environ.get("PAGE_ACCESS_TOKEN", "").strip()
    if not tok:
        raise RuntimeError("PAGE_ACCESS_TOKEN nao encontrado (nem passado, nem no ambiente).")
    return tok


def _page_id(token):
    """Descobre o ID da propria Pagina a partir do token de pagina."""
    r = httpx.get(
        f"{GRAPH}/me",
        params={"fields": "id,name", "access_token": token},
        timeout=TIMEOUT,
    )
    dados = r.json()
    if "id" not in dados:
        raise RuntimeError(f"Nao consegui descobrir o ID da Pagina: {dados}")
    print(f"[facebook] Pagina: {dados.get('name')} (id {dados['id']})")
    return dados["id"]


def _publicar_foto_unica(page_id, token, url_imagem, legenda):
    r = httpx.post(
        f"{GRAPH}/{page_id}/photos",
        data={"url": url_imagem, "caption": legenda, "access_token": token},
        timeout=TIMEOUT,
    )
    dados = r.json()
    post = dados.get("post_id") or dados.get("id")
    if not post:
        raise RuntimeError(f"Falha ao publicar foto no Facebook: {dados}")
    return post


def _subir_foto_sem_publicar(page_id, token, url_imagem):
    """Sobe a foto como NAO publicada e devolve o media_fbid (pro carrossel)."""
    r = httpx.post(
        f"{GRAPH}/{page_id}/photos",
        data={"url": url_imagem, "published": "false", "access_token": token},
        timeout=TIMEOUT,
    )
    dados = r.json()
    if "id" not in dados:
        raise RuntimeError(f"Falha ao subir imagem do carrossel: {dados}")
    return dados["id"]


def _publicar_carrossel(page_id, token, urls_imagens, legenda):
    media_fbids = [_subir_foto_sem_publicar(page_id, token, u) for u in urls_imagens]
    data = {"message": legenda, "access_token": token}
    for i, fbid in enumerate(media_fbids):
        data[f"attached_media[{i}]"] = json.dumps({"media_fbid": fbid})
    r = httpx.post(f"{GRAPH}/{page_id}/feed", data=data, timeout=TIMEOUT)
    dados = r.json()
    if "id" not in dados:
        raise RuntimeError(f"Falha ao publicar carrossel no Facebook: {dados}")
    return dados["id"]


def publicar_no_facebook(imagens, legenda, token=None):
    """
    imagens : 1 URL (str) = foto unica  |  lista de URLs = carrossel.
              As URLs precisam ser publicas (raw.githubusercontent.com,
              cdn.shopify.com, etc.) - o Facebook baixa a imagem da URL.
    legenda : texto do post (a mesma legenda usada no Instagram).
    token   : token da Pagina. Se None, le de os.environ["PAGE_ACCESS_TOKEN"].

    Retorna o ID do post publicado. Levanta erro se algo falhar.
    """
    if isinstance(imagens, str):
        imagens = [imagens]
    imagens = [u for u in imagens if u]
    if not imagens:
        raise RuntimeError("Nenhuma imagem informada para publicar no Facebook.")

    tok = _token(token)
    page_id = _page_id(tok)

    if len(imagens) == 1:
        post_id = _publicar_foto_unica(page_id, tok, imagens[0], legenda)
    else:
        post_id = _publicar_carrossel(page_id, tok, imagens, legenda)

    print(f"[facebook] Publicado com sucesso. Post: {post_id}")
    return post_id
