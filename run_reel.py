# -*- coding: utf-8 -*-
"""
Gera e publica um REEL (vídeo 9:16) do produto do dia no Instagram.
Reusa frasco limpo + foco + compliance. Sem links/figurinhas: CTA na imagem.
Fluxo Reels: cria container (media_type=REELS) -> espera FINISHED -> publica.
"""
import base64
import os
import time
from datetime import datetime

import requests

from src import config
from src import util_net as net
from src import historico
from src.image import composer
from src.image.story_arte import montar_story
from src.image.video import gerar_reel
from src.agents.textos_informativo import gerar_textos
from src.compliance import focos_permitidos, garantir
from src.image.foto import melhor_recorte, urls_produto
from src.social_shopping import tags_para, ids_shopify
import json

try:
    from src.agents.arte_textos import escolher_foco
except Exception:
    def escolher_foco(indice, n):
        return ["PELE", "CABELO", "SAUDE"][(indice // max(n, 1)) % 3]

API = "https://graph.facebook.com/v25.0"


def _carregar():
    try:
        from src import catalogo
        p = catalogo.carregar()
        if p:
            return p
    except Exception as e:
        print("aviso: catalogo.carregar falhou:", e)
    out, page = [], 1
    while page <= 10:
        r = net.get(f"https://eikovida.com/products.json?limit=250&page={page}", timeout=30)
        data = r.json().get("products", [])
        if not data:
            break
        out += data; page += 1
    return out


def _nome(p):
    for k in ("nome", "titulo", "title"):
        if p.get(k):
            return p[k]
    return "Produto"


def hospedar_video(path):
    """Sobe o MP4 no repo de imagens (GitHub) e devolve a URL publica (raw)."""
    repo = os.environ.get("GH_IMAGES_REPO") or getattr(config, "GH_IMAGES_REPO", "")
    token = os.environ.get("GH_TOKEN") or getattr(config, "GH_TOKEN", "")
    nome = f"reels/reel_{int(time.time())}.mp4"
    data = base64.b64encode(open(path, "rb").read()).decode()
    r = net.put(
        f"https://api.github.com/repos/{repo}/contents/{nome}",
        headers={"Authorization": f"token {token}", "Accept": "application/vnd.github+json"},
        json={"message": "reel eikovida", "content": data}, timeout=180).json()
    if "content" not in r:
        raise RuntimeError(f"Hospedagem do video falhou: {r.get('message', r)}")
    return r["content"]["download_url"]


def _criar_container(video_url, caption, product_tags):
    params = {"media_type": "REELS", "video_url": video_url, "caption": caption,
              "share_to_feed": "true", "access_token": config.PAGE_ACCESS_TOKEN}
    if product_tags:
        params["product_tags"] = json.dumps(product_tags)
    return net.post(f"{API}/{config.IG_ACCOUNT_ID}/media", params=params, timeout=60).json()


def publicar_reel(video_url, caption, product_tags=None):
    cont = _criar_container(video_url, caption, product_tags)
    if "error" in cont and product_tags:
        # se a etiqueta falhar (ex: permissao), publica o reel sem etiqueta
        print("aviso: etiqueta de produto falhou, publicando sem ela:", cont["error"].get("message"))
        cont = _criar_container(video_url, caption, None)
    if "error" in cont:
        raise RuntimeError(f"Container reel: {cont['error'].get('message')}")
    cid = cont["id"]
    # espera o video processar (status FINISHED) - ate ~5 min
    for _ in range(20):
        time.sleep(15)
        st = net.get(f"{API}/{cid}", params={"fields": "status_code",
                          "access_token": config.PAGE_ACCESS_TOKEN}, timeout=30).json()
        code = st.get("status_code")
        print("status:", code)
        if code == "FINISHED":
            break
        if code == "ERROR":
            raise RuntimeError("Processamento do reel falhou (ERROR).")
    pub = net.post(f"{API}/{config.IG_ACCOUNT_ID}/media_publish",
                        params={"creation_id": cid, "access_token": config.PAGE_ACCESS_TOKEN},
                        timeout=60).json()
    if "error" in pub:
        raise RuntimeError(f"Publish reel: {pub['error'].get('message')}")
    return pub.get("id")


def main():
    produtos = _carregar()
    if not produtos:
        raise SystemExit("ERRO: nenhum produto encontrado.")
    indice = datetime.now().timetuple().tm_yday
    n = len(produtos)
    produto = None
    for passo in range(n):
        cand = produtos[(indice + passo) % n]
        if urls_produto(cand):
            produto = cand; break
    if not produto:
        raise SystemExit("ERRO: nenhum produto com imagem.")

    nome = _nome(produto)
    foco = escolher_foco(indice, n)
    perm = focos_permitidos(nome)
    if foco not in perm:
        foco = perm[0]

    frasco, sc = melhor_recorte(produto, lambda u: net.get(u, timeout=30).content, composer)
    if frasco is None:
        raise SystemExit("ERRO: nao consegui recortar nenhuma foto.")

    t = gerar_textos(nome, "", foco, None)
    frame = montar_story(frasco, nome, foco, t["tagline3"])
    gerar_reel(frame, "reel.mp4", dur=8, fps=30)

    from src.image.story_arte import limpar_nome
    nm = limpar_nome(nome)
    legenda = (f"{nm} — {' • '.join(t['tagline3'])}.\n\n"
               "100% puro e natural, prensado a frio. Conheça no link da bio.\n\n"
               "#eikovida #oleosnaturais #cosmeticosnaturais #cuidadonatural #belezanatural")
    legenda = garantir(legenda, f"{nm}. 100% puro e natural. Link na bio.\n\n#eikovida #oleosnaturais")

    url = hospedar_video("reel.mp4")
    print("Reel hospedado:", url)
    tags = tags_para(nome, retailer_ids=ids_shopify(produto))   # casa o item EXATO (30ml/120ml/kit)
    print("Etiqueta de produto:", "sim" if tags else "nao encontrada")
    media_id = publicar_reel(url, legenda, product_tags=tags)
    historico.registrar("Reel", nm, media_id, ("com etiqueta" if tags else foco))
    print(f"OK -> reel publicado | produto: {nm} | foco: {foco} | id: {media_id}")


if __name__ == "__main__":
    main()
