# -*- coding: utf-8 -*-
"""
Publica o STORY do produto do dia no Instagram (media_type=STORIES).
Reusa a hospedagem (ImageGenerator.hospedar) e as credenciais (src.config).
Sem caption, sem link clicavel: o CTA "ACESSE O LINK NA BIO" fica na imagem.
Roda sozinho quando o "Ciclo Diario" termina (workflow publicar-story.yml).
"""
import base64
import io
import time
from datetime import datetime

import requests

from src import config
from src.image import composer
from src.image.generator import ImageGenerator
from src.image.story_arte import montar_story
from src.agents.textos_informativo import gerar_textos
from src.compliance import focos_permitidos
from src.image.foto import melhor_recorte, urls_produto

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
        r = requests.get(f"https://eikovida.com/products.json?limit=250&page={page}", timeout=30)
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


def _url(p):
    if p.get("imagem"):
        return p["imagem"]
    for k in ("imagens", "images"):
        arr = p.get(k) or []
        if arr:
            x = arr[0]
            return x.get("src") or x.get("url") if isinstance(x, dict) else x
    return None


def publicar_story(image_url):
    """Cria container STORIES (sem caption), aguarda e publica."""
    cont = requests.post(f"{API}/{config.IG_ACCOUNT_ID}/media",
                         params={"image_url": image_url, "media_type": "STORIES",
                                 "access_token": config.PAGE_ACCESS_TOKEN}, timeout=60).json()
    if "error" in cont:
        raise RuntimeError(f"Container story: {cont['error'].get('message')}")
    time.sleep(8)
    pub = requests.post(f"{API}/{config.IG_ACCOUNT_ID}/media_publish",
                        params={"creation_id": cont["id"],
                                "access_token": config.PAGE_ACCESS_TOKEN}, timeout=60).json()
    if "error" in pub:
        raise RuntimeError(f"Publish story: {pub['error'].get('message')}")
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

    # escolhe a FOTO MAIS LIMPA do produto (sem splash), igual ao feed
    frasco, sc = melhor_recorte(produto, lambda u: requests.get(u, timeout=30).content, composer)
    if frasco is None:
        raise SystemExit("ERRO: nao consegui recortar nenhuma foto.")
    print(f"Foto escolhida (score {sc:.2f} - menor=mais limpo)")
    t = gerar_textos(nome, "", foco, None)
    story = montar_story(frasco, nome, foco, t["tagline3"])

    # hospeda (mesma hospedagem do feed) e publica
    buf = io.BytesIO(); story.save(buf, "PNG")
    b64 = base64.b64encode(buf.getvalue()).decode()
    image_url = ImageGenerator().hospedar(b64)
    print("Story hospedado:", image_url)

    media_id = publicar_story(image_url)
    print(f"OK -> story publicado | produto: {nome} | foco: {foco} | id: {media_id}")


if __name__ == "__main__":
    main()
