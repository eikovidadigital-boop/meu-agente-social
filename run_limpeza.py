# -*- coding: utf-8 -*-
"""
Manutencao: apaga do repo de imagens (GH_IMAGES_REPO) as imagens antigas que o
sistema gerou (img_<epoch>.jpg), liberando espaco e mantendo o repo leve/rapido.
Por padrao remove imagens com mais de 30 dias (o Instagram ja baixou e guardou a
copia ao publicar — a imagem no repo so serve no momento da publicacao).

Roda sozinho via .github/workflows/limpeza.yml (semanal). Tudo em try/except:
falha de manutencao NUNCA atrapalha publicacao.
"""
import os
import re
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from src import config
from src import util_net as net

DIAS = int(os.environ.get("LIMPEZA_DIAS", "30"))
API = "https://api.github.com"


def _headers():
    return {"Authorization": f"token {config.GH_TOKEN}",
            "Accept": "application/vnd.github+json"}


def _listar(repo):
    """Todas as imagens do repo (pagina de 100 em 100)."""
    itens, pagina = [], 1
    while pagina <= 50:
        r = net.get(f"{API}/repos/{repo}/contents",
                    headers=_headers(),
                    params={"per_page": 100, "page": pagina}, timeout=60)
        lote = r.json()
        if not isinstance(lote, list) or not lote:
            if isinstance(lote, dict) and lote.get("message"):
                print("aviso limpeza:", lote.get("message"))
            break
        itens += lote
        if len(lote) < 100:
            break
        pagina += 1
    return itens


def main():
    repo = config.GH_IMAGES_REPO
    if not repo or not config.GH_TOKEN:
        print("limpeza: GH_IMAGES_REPO/GH_TOKEN ausentes — nada a fazer."); return
    limite = time.time() - DIAS * 86400
    itens = _listar(repo)
    apagados = 0
    for it in itens:
        nome = it.get("name", "")
        m = re.match(r"img_(\d+)\.(jpg|jpeg|png)$", nome)
        if not m:
            continue                      # so mexe nas imagens geradas pelo sistema
        if int(m.group(1)) >= limite:
            continue                      # ainda recente, mantem
        try:
            d = net._try(__import__("requests").delete,
                         f"{API}/repos/{repo}/contents/{nome}",
                         headers=_headers(),
                         json={"message": f"limpeza: remove {nome}", "sha": it["sha"]},
                         timeout=30)
            if getattr(d, "status_code", 500) < 300:
                apagados += 1
        except Exception as e:
            print(f"aviso: nao removeu {nome}: {e}")
    print(f"limpeza concluida: {apagados} imagem(ns) com mais de {DIAS} dias removida(s) de {len(itens)} no repo.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("aviso: limpeza falhou (sem impacto na publicacao):", e)
