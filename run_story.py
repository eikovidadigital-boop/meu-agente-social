# -*- coding: utf-8 -*-
"""
Publica o STORY do produto do dia no Instagram (media_type=STORIES).
Reusa a hospedagem (ImageGenerator.hospedar) e as credenciais (src.config).
Sem caption, sem link clicavel: o CTA "ACESSE O LINK NA BIO" fica na imagem.
Roda sozinho quando o "Ciclo Diario" termina (workflow publicar-story.yml).
"""
import base64
import io
import re
import time
from datetime import datetime

import requests

from src import config
from src import util_net as net
from src import historico
from src.image import composer
from src.image.generator import ImageGenerator
from src.image.story_arte import montar_story, limpar_nome
from src import fundos, rotacao
from src.agents.textos_informativo import gerar_textos
from src.compliance import focos_permitidos, foco_cosmetico
from src.image.foto import melhor_recorte, urls_produto

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


def _descricao(p):
    """Descricao real do produto, cobrindo os dois formatos (catalogo e products.json)."""
    d = p.get("descricao") or p.get("body_html") or p.get("description") or ""
    d = re.sub(r"<[^>]+>", " ", d)        # tira HTML
    return re.sub(r"\s+", " ", d).strip()


def _tags(p):
    """Tags + tipo do produto (pistas extras pro foco: 'Shampoo', 'Kit', etc.)."""
    t = p.get("tags")
    if isinstance(t, list):
        t = " ".join(t)
    tipo = p.get("product_type") or p.get("tipo") or ""
    return f"{t or ''} {tipo}".strip()


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
    cont = net.post(f"{API}/{config.IG_ACCOUNT_ID}/media",
                         params={"image_url": image_url, "media_type": "STORIES",
                                 "access_token": config.PAGE_ACCESS_TOKEN}, timeout=60).json()
    if "error" in cont:
        raise RuntimeError(f"Container story: {cont['error'].get('message')}")
    time.sleep(8)
    pub = net.post(f"{API}/{config.IG_ACCOUNT_ID}/media_publish",
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
    indice_prod = rotacao.indice_produto("story")   # nao repete produto (varia por horario+formato)
    n = len(produtos)
    produto = None
    for passo in range(n):
        cand = produtos[(indice_prod + passo) % n]
        if urls_produto(cand):
            produto = cand; break
    if not produto:
        raise SystemExit("ERRO: nenhum produto com imagem.")

    nome = _nome(produto)
    descricao = _descricao(produto)
    tags = _tags(produto)
    # FOCO pela DESCRICAO REAL do produto (igual ao feed) — nunca mais sorteio cego.
    foco = foco_cosmetico(nome, descricao, tags)    # CABELO ou PELE, NUNCA saude
    perm = focos_permitidos(nome)
    if foco not in perm:
        foco = perm[0]
    print(f"Story | produto: {nome} | foco: {foco}")

    # escolhe a FOTO MAIS LIMPA do produto (sem splash), igual ao feed
    frasco, sc = melhor_recorte(produto, lambda u: net.get(u, timeout=30).content, composer)
    if frasco is None:
        raise SystemExit("ERRO: nao consegui recortar nenhuma foto.")
    print(f"Foto escolhida (score {sc:.2f} - menor=mais limpo)")
    t = gerar_textos(nome, descricao[:600], foco, None)   # estuda a descricao real
    fundo = fundos.fundo_do_dia(indice, limpar_nome(nome))   # fundo de IA (rotaciona 4 estilos)
    story = montar_story(frasco, nome, foco, t["tagline3"], fundo=fundo)

    # hospeda (mesma hospedagem do feed) e publica
    buf = io.BytesIO(); story.save(buf, "PNG")
    b64 = base64.b64encode(buf.getvalue()).decode()
    image_url = ImageGenerator().hospedar(b64)
    print("Story hospedado:", image_url)

    media_id = publicar_story(image_url)
    historico.registrar("Story", nome, media_id, foco)
    print(f"OK -> story publicado | produto: {nome} | foco: {foco} | id: {media_id}")


if __name__ == "__main__":
    main()
