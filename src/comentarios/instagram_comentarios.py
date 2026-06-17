# -*- coding: utf-8 -*-
"""
Conversa com a Graph API do Instagram (v25.0):
- descobre o IG User ID a partir do PAGE_ACCESS_TOKEN
- lista posts recentes e seus comentários
- responde comentários
"""
import time
import httpx

API = "https://graph.facebook.com/v25.0"


def _get(path, params):
    r = httpx.get(f"{API}/{path}", params=params, timeout=30)
    r.raise_for_status()
    return r.json()


def descobrir_ig_user_id(token: str):
    """
    Descobre automaticamente o ID da conta Instagram Business
    ligada à página do Facebook (não precisa de secret extra).
    """
    contas = _get("me/accounts", {"access_token": token}).get("data", [])
    for pagina in contas:
        page_id = pagina.get("id")
        try:
            info = _get(page_id, {
                "fields": "instagram_business_account",
                "access_token": token,
            })
            iba = info.get("instagram_business_account")
            if iba and iba.get("id"):
                return iba["id"]
        except Exception:
            continue
    return None


def meu_username(ig_user_id: str, token: str):
    """Retorna o @username da própria conta (pra não responder a si mesmo)."""
    try:
        info = _get(ig_user_id, {"fields": "username", "access_token": token})
        return (info.get("username") or "").lower()
    except Exception:
        return ""


def listar_posts_recentes(ig_user_id: str, token: str, limite: int = 20):
    """Últimos posts: id, legenda, link e data."""
    dados = _get(f"{ig_user_id}/media", {
        "fields": "id,caption,permalink,timestamp",
        "limit": limite,
        "access_token": token,
    }).get("data", [])
    return dados


def listar_comentarios(media_id: str, token: str):
    """Comentários de um post: id, texto, autor e data."""
    try:
        dados = _get(f"{media_id}/comments", {
            "fields": "id,text,username,timestamp",
            "limit": 50,
            "access_token": token,
        }).get("data", [])
        return dados
    except Exception as e:
        print(f"[ig] erro ao ler comentários de {media_id}: {e}")
        return []


def responder_comentario(comment_id: str, mensagem: str, token: str):
    """Posta uma resposta pública pendurada no comentário."""
    r = httpx.post(f"{API}/{comment_id}/replies", data={
        "message": mensagem,
        "access_token": token,
    }, timeout=30)
    if r.status_code >= 400:
        print(f"[ig] falha ao responder {comment_id}: {r.text}")
        return False
    return True
