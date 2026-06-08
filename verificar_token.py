# -*- coding: utf-8 -*-
"""
Checa a validade do token do Instagram/Facebook e AVISA antes de vencer.
Roda 1x por semana. Se o token estiver perto de vencer ou invalido, o job
falha de proposito -> o GitHub manda e-mail de falha, e voce renova a tempo.
"""
import time
import requests

from src import config

API = "https://graph.facebook.com"
DIAS_ALERTA = 10


def main():
    tok = config.PAGE_ACCESS_TOKEN
    # 1) tenta descobrir a data de expiracao
    try:
        r = requests.get(f"{API}/debug_token",
                         params={"input_token": tok, "access_token": tok}, timeout=30).json()
        data = r.get("data", {})
    except Exception:
        data = {}

    if data.get("is_valid") is False:
        raise SystemExit("ERRO: token do Instagram INVALIDO. Renove o PAGE_ACCESS_TOKEN ja.")

    exp = data.get("expires_at") or data.get("data_access_expires_at") or 0
    if exp and exp > 0:
        dias = (exp - time.time()) / 86400
        print(f"Token valido. Faltam ~{dias:.0f} dias para vencer.")
        if dias <= DIAS_ALERTA:
            raise SystemExit(f"ATENCAO: o token vence em ~{dias:.0f} dias. "
                             "Renove o PAGE_ACCESS_TOKEN agora (processo de 3 passos).")
        return

    # 2) sem data: faz um teste real com o token
    h = requests.get(f"{API}/v25.0/{config.IG_ACCOUNT_ID}",
                     params={"fields": "id", "access_token": tok}, timeout=30).json()
    if "error" in h:
        raise SystemExit(f"ERRO: o token nao funciona mais: {h['error'].get('message')}. "
                         "Renove o PAGE_ACCESS_TOKEN.")
    print("Token valido (sem data de expiracao informada). Tudo certo.")


if __name__ == "__main__":
    main()
