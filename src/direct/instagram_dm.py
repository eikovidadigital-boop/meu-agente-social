# -*- coding: utf-8 -*-
"""
Acesso ao Direct (DM) do Instagram via Graph API.

Token usado: PAGE_ACCESS_TOKEN (token de PAGINA, o mesmo do resto do sistema).
Como o token e de pagina, o IG user id e descoberto por /me?fields=instagram_business_account
(se config.IG_ACCOUNT_ID nao estiver definido).

Funciona por POLLING (puxa as conversas a cada execucao), sem webhook/servidor.

Regra dura da Meta respeitada pelo run: so se responde mensagem do cliente dentro
da janela de 24h. Como o workflow roda a cada 15 min, sempre dentro da janela.
"""
from src import config
from src import util_net as net

API = "https://graph.facebook.com/v25.0"


def _token():
    return getattr(config, "PAGE_ACCESS_TOKEN", "") or ""


def descobrir_ig_user_id(token=None):
    """Retorna o IG business account id. Usa config.IG_ACCOUNT_ID se existir;
    senao descobre pelo token de pagina."""
    fixo = getattr(config, "IG_ACCOUNT_ID", "") or ""
    if fixo:
        return str(fixo)
    token = token or _token()
    r = net.get(f"{API}/me", params={"fields": "instagram_business_account",
                                     "access_token": token}, timeout=30).json()
    iba = (r or {}).get("instagram_business_account") or {}
    if not iba.get("id"):
        raise RuntimeError(f"Nao achei a conta do Instagram pelo token: {r}")
    return iba["id"]


def listar_conversas(ig_id, token=None, limite=30):
    """Lista as conversas recentes do Direct (Instagram)."""
    token = token or _token()
    r = net.get(f"{API}/{ig_id}/conversations",
                params={"platform": "instagram",
                        "fields": "id,updated_time",
                        "limit": limite,
                        "access_token": token}, timeout=60).json()
    if "error" in r:
        raise RuntimeError(f"listar_conversas: {r['error'].get('message')}")
    return r.get("data", [])


def listar_mensagens(conversa_id, token=None, limite=15):
    """Lista as mensagens de uma conversa (mais recentes primeiro)."""
    token = token or _token()
    r = net.get(f"{API}/{conversa_id}",
                params={"fields": f"messages.limit({limite}){{id,from,to,message,created_time}}",
                        "access_token": token}, timeout=60).json()
    if "error" in r:
        raise RuntimeError(f"listar_mensagens: {r['error'].get('message')}")
    return (r.get("messages") or {}).get("data", [])


def enviar_mensagem(ig_id, destinatario_id, texto, token=None):
    """Envia uma mensagem de texto para o cliente (dentro da janela de 24h)."""
    token = token or _token()
    r = net.post(f"{API}/{ig_id}/messages",
                 json={"recipient": {"id": destinatario_id},
                       "message": {"text": texto}},
                 params={"access_token": token}, timeout=60).json()
    if "error" in r:
        raise RuntimeError(f"enviar_mensagem: {r['error'].get('message')}")
    return r.get("message_id") or r.get("id") or "ok"
