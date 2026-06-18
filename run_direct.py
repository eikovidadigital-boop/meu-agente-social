# -*- coding: utf-8 -*-
"""
run_direct.py — Atendimento automatico no DIRECT (DM) do Instagram.

Roda pelo GitHub Actions a cada 15 min:
1. Descobre a conta do Instagram pelo token.
2. Lista as conversas recentes do Direct.
3. Em cada conversa, olha a ULTIMA mensagem:
   - se a ultima ja e nossa, a conversa esta em dia -> pula;
   - se e do cliente, ainda nao respondida e dentro de 24h -> responde.
4. Classifica + detector de intencao de compra (link direto do produto) + compliance.
5. Marca como respondida (data/direct_respondidos.txt, commitado pelo workflow).

Janela da Meta: so se responde DM do cliente dentro de 24h. Como roda a cada 15 min,
sempre dentro da janela.
"""
from datetime import datetime, timezone

from src.direct import instagram_dm as ig
from src.direct import produtos as prod
from src.direct import estado
from src.direct import cerebro

JANELA_HORAS = 24


def _horas_desde(ts):
    if not ts:
        return 0.0
    for fmt in ("%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%S.%f%z"):
        try:
            dt = datetime.strptime(ts, fmt)
            return (datetime.now(timezone.utc) - dt).total_seconds() / 3600.0
        except Exception:
            pass
    try:
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        return (datetime.now(timezone.utc) - dt).total_seconds() / 3600.0
    except Exception:
        return 0.0  # nao deu pra ler -> trata como recente (responde)


def main():
    token = ig._token()
    if not token:
        raise SystemExit("ERRO: PAGE_ACCESS_TOKEN nao configurado.")

    ig_id = ig.descobrir_ig_user_id(token)
    print(f"[direct] Conta IG: {ig_id}")

    produtos = prod.carregar_produtos()
    cardapio = prod.cardapio(produtos)
    site_ok = prod.site_no_ar()
    print(f"[direct] {len(produtos)} produtos no catalogo | site {'no ar' if site_ok else 'fora'}")

    respondidos = estado.carregar()
    conversas = ig.listar_conversas(ig_id, token)
    print(f"[direct] {len(conversas)} conversas recentes")

    enviadas = 0
    for c in conversas:
        try:
            msgs = ig.listar_mensagens(c["id"], token)
        except Exception as e:
            print(f"  aviso: falha ao ler conversa {c.get('id')}: {e}")
            continue
        if not msgs:
            continue

        topo = msgs[0]  # mensagem mais recente
        autor = (topo.get("from") or {}).get("id", "")
        mid = topo.get("id", "")
        texto = (topo.get("message") or "").strip()

        if autor == str(ig_id):
            continue                      # ultima e nossa -> conversa em dia
        if not mid or mid in respondidos:
            continue                      # ja respondida
        if _horas_desde(topo.get("created_time")) > JANELA_HORAS:
            continue                      # fora da janela de 24h
        if not texto:
            estado.marcar(mid); continue  # anexo sem texto -> ignora

        try:
            r = cerebro.pensar(texto, produtos, cardapio, site_ok)
        except Exception as e:
            print(f"  aviso: cerebro falhou em {mid}: {e}")
            continue

        if r["tipo"] == "IGNORAR" or not r["texto"]:
            estado.marcar(mid)            # marca spam pra nao reprocessar sempre
            continue

        try:
            ig.enviar_mensagem(ig_id, autor, r["texto"], token)
            estado.marcar(mid)
            enviadas += 1
            print(f"  ✓ DM [{r['tipo']}] respondida.")
        except Exception as e:
            print(f"  ✗ falha ao responder {mid}: {e}")

    print(f"[fim] {enviadas} DMs respondidas nesta execucao.")


if __name__ == "__main__":
    main()
