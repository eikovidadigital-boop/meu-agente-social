# -*- coding: utf-8 -*-
"""
Relatorio mensal de desempenho do Instagram (Graph API v25.0).
Gera um resumo SIMPLES e legivel (pro Paulo, nao-tecnico): quantos seguidores,
quantos posts no mes, quais posts mais bombaram, e o alcance/visitas quando a
API liberar. Tudo defensivo: cada metrica em try/except — se a Meta mudar algo,
o relatorio ainda sai com o que der.

Injecao de dependencia: `buscar` pode ser substituida em teste.
"""
import os

try:
    from src import config, tempo
    from src import util_net as net
except ImportError:
    import config, tempo
    import util_net as net

API = "https://graph.facebook.com/v25.0"


def _tok():
    return os.environ.get("PAGE_ACCESS_TOKEN") or getattr(config, "PAGE_ACCESS_TOKEN", "")


def descobrir_ig_id(buscar=None):
    """Usa o IG_ACCOUNT_ID se houver; senao descobre pela pagina (token de pagina)."""
    igid = os.environ.get("IG_ACCOUNT_ID") or getattr(config, "IG_ACCOUNT_ID", "")
    if igid:
        return igid
    buscar = buscar or _padrao_buscar
    d = buscar(f"{API}/me", {"fields": "instagram_business_account", "access_token": _tok()})
    return (d.get("instagram_business_account") or {}).get("id", "")


def _padrao_buscar(url, params):
    return net.get(url, params=params, timeout=30).json()


def coletar(buscar=None, ig_id=None, dias=30):
    """Junta os dados do mes num dict simples. Nunca levanta: devolve o que der."""
    buscar = buscar or _padrao_buscar
    ig_id = ig_id or descobrir_ig_id(buscar)
    tok = _tok()
    dados = {"ig_id": ig_id, "mes": tempo.mes_ref(), "seguidores": None,
             "total_posts_conta": None, "alcance_mes": None, "visitas_perfil": None,
             "posts": []}
    if not ig_id:
        dados["erro"] = "IG_ID nao encontrado"
        return dados

    # 1) perfil (confiavel)
    try:
        p = buscar(f"{API}/{ig_id}", {"fields": "followers_count,media_count", "access_token": tok})
        dados["seguidores"] = p.get("followers_count")
        dados["total_posts_conta"] = p.get("media_count")
    except Exception as e:
        print("aviso perfil:", e)

    # 2) alcance/visitas do mes (pode mudar na API -> defensivo)
    for metric, chave in (("reach", "alcance_mes"), ("profile_views", "visitas_perfil")):
        try:
            r = buscar(f"{API}/{ig_id}/insights",
                       {"metric": metric, "period": "days_28",
                        "metric_type": "total_value", "access_token": tok})
            vals = (r.get("data") or [])
            if vals:
                tv = vals[0].get("total_value") or {}
                dados[chave] = tv.get("value") if isinstance(tv, dict) else vals[0].get("values", [{}])[-1].get("value")
        except Exception as e:
            print(f"aviso {metric}:", e)

    # 3) posts recentes + engajamento (likes/comentarios sao confiaveis)
    try:
        corte = tempo.agora().timestamp() - dias * 86400
        m = buscar(f"{API}/{ig_id}/media",
                   {"fields": "id,caption,timestamp,permalink,like_count,comments_count,media_type",
                    "limit": 50, "access_token": tok})
        for it in (m.get("data") or []):
            ts = it.get("timestamp", "")
            posts = dados["posts"]
            posts.append({
                "id": it.get("id"), "permalink": it.get("permalink", ""),
                "tipo": it.get("media_type", ""), "quando": ts[:10],
                "curtidas": it.get("like_count") or 0,
                "comentarios": it.get("comments_count") or 0,
                "legenda": (it.get("caption") or "").split("\n")[0][:60],
            })
    except Exception as e:
        print("aviso media:", e)
    return dados


def montar_markdown(d):
    """Transforma os dados num texto bem direto pro Paulo."""
    mes = d.get("mes", "")
    L = [f"# Relatorio EikoVida — {mes}", ""]
    if d.get("erro"):
        L += [f"> Nao consegui puxar os dados: {d['erro']}.", ""]
    L += ["## Visao geral",
          f"- Seguidores: **{d.get('seguidores') if d.get('seguidores') is not None else '—'}**",
          f"- Posts publicados (total da conta): **{d.get('total_posts_conta') if d.get('total_posts_conta') is not None else '—'}**",
          f"- Alcance (ult. 28 dias): **{d.get('alcance_mes') if d.get('alcance_mes') is not None else '— (a Meta nao liberou esta metrica)'}**",
          f"- Visitas ao perfil (ult. 28 dias): **{d.get('visitas_perfil') if d.get('visitas_perfil') is not None else '—'}**",
          ""]
    posts = sorted(d.get("posts", []), key=lambda p: p["curtidas"] + p["comentarios"], reverse=True)
    L += [f"## Posts recentes ({len(posts)})", ""]
    if posts:
        L += ["### 🏆 Os 5 que mais bombaram", ""]
        for i, p in enumerate(posts[:5], 1):
            L.append(f"{i}. **{p['curtidas']} curtidas · {p['comentarios']} coment.** — "
                     f"{p['legenda'] or '(sem legenda)'} ({p['quando']}) — [ver]({p['permalink']})")
        L.append("")
        media_eng = sum(p["curtidas"] + p["comentarios"] for p in posts) / max(1, len(posts))
        L += ["### Resumo", f"- Engajamento medio por post: **{media_eng:.0f}** (curtidas + comentarios)", ""]
    else:
        L += ["_Sem posts no periodo (ou a API nao retornou)._", ""]
    L += ["---", "_Gerado automaticamente pelo sistema meu-agente-social._"]
    return "\n".join(L)
