# -*- coding: utf-8 -*-
"""
Publica um CARROSSEL (album) no feed do Instagram (media_type=CAROUSEL).
Intercala 3 tipos automaticamente: beneficios -> curiosidades -> modo de usar.
- Escolhe o produto pela rotacao (nao repete com feed/story/reel).
- Conteudo gerado por IA (Anthropic) com reserva segura, revisado pelas regras ANVISA.
- Usa a FOTO REAL do produto e a mesma hospedagem (ImageGenerator.hospedar).
Roda pelo workflow publicar-carrossel.yml.
"""
import base64
import io
import json
import os
import time
from datetime import datetime

import requests

from src import config
from src import util_net as net
from src import historico, rotacao
from src.image import composer
from src.image.generator import ImageGenerator
from src.image.story_arte import limpar_nome
from src.image.carrossel_arte import montar_carrossel
from src.image.foto import melhor_recorte, urls_produto
from src.carrossel_conteudo import gerar_itens, legenda_carrossel
from src.social_shopping import tags_para, ids_shopify

API = "https://graph.facebook.com/v25.0"


def _carregar():
    from src import produtos
    return produtos.carregar()


def _nome(p):
    for k in ("nome", "titulo", "title"):
        if p.get(k):
            return p[k]
    return "Produto"


def _llm():
    """Cliente de IA (Anthropic) usando a chave do projeto. Sem chave -> None (usa reserva)."""
    key = getattr(config, "ANTHROPIC_API_KEY", "") or os.environ.get("ANTHROPIC_API_KEY", "")
    if not key:
        print("IA indisponivel (sem ANTHROPIC_API_KEY) -> conteudo padrao")
        return None
    modelo = os.environ.get("ANTHROPIC_MODEL", "claude-3-5-haiku-latest")

    def responder(prompt):
        r = net.post("https://api.anthropic.com/v1/messages",
                     headers={"x-api-key": key, "anthropic-version": "2023-06-01",
                              "content-type": "application/json"},
                     json={"model": modelo, "max_tokens": 600,
                           "messages": [{"role": "user", "content": prompt}]},
                     timeout=45)
        d = r.json()
        if "error" in d:
            raise RuntimeError(d["error"].get("message", "erro IA"))
        return "".join(b.get("text", "") for b in d.get("content", []) if b.get("type") == "text")

    obj = type("LLM", (), {})()
    obj.responder = responder
    return obj


def _criar_slide(u, tags):
    p = {"image_url": u, "is_carousel_item": "true", "access_token": config.PAGE_ACCESS_TOKEN}
    if tags:
        p["product_tags"] = json.dumps(tags)
    return net.post(f"{API}/{config.IG_ACCOUNT_ID}/media", params=p, timeout=60).json()


def publicar_carrossel(urls, legenda, tags_por_slide=None):
    """Cria um container por slide (is_carousel_item), agrupa em CAROUSEL e publica.
    tags_por_slide: dict {indice_do_slide: etiquetas}. Se a etiqueta falhar num slide,
    publica aquele slide sem etiqueta (nao perde o carrossel)."""
    tags_por_slide = tags_por_slide or {}
    children = []
    for i, u in enumerate(urls):
        tags = tags_por_slide.get(i)
        c = _criar_slide(u, tags)
        if "error" in c and tags:
            print(f"aviso: etiqueta no slide {i+1} falhou, publicando sem ela:",
                  c["error"].get("message"))
            c = _criar_slide(u, None)
        if "error" in c:
            raise RuntimeError(f"Slide {i+1}: {c['error'].get('message')}")
        children.append(c["id"]); time.sleep(2)
    cont = net.post(f"{API}/{config.IG_ACCOUNT_ID}/media",
                    params={"media_type": "CAROUSEL", "children": ",".join(children),
                            "caption": legenda, "access_token": config.PAGE_ACCESS_TOKEN}, timeout=60).json()
    if "error" in cont:
        raise RuntimeError(f"Container carrossel: {cont['error'].get('message')}")
    time.sleep(8)
    pub = net.post(f"{API}/{config.IG_ACCOUNT_ID}/media_publish",
                   params={"creation_id": cont["id"], "access_token": config.PAGE_ACCESS_TOKEN}, timeout=60).json()
    if "error" in pub:
        raise RuntimeError(f"Publish carrossel: {pub['error'].get('message')}")
    return pub.get("id")


def main():
    from src import produtos as _prod
    lista = _carregar()
    if not lista:
        raise SystemExit("ERRO: nenhum produto encontrado.")

    indice_prod = rotacao.indice_produto("carrossel")   # nao repete com feed/story/reel
    produto = _prod.escolher(lista, "carrossel", indice_prod)   # nao repete o ingrediente
    if not produto:
        raise SystemExit("ERRO: nenhum produto com imagem.")

    nome = _nome(produto)
    nome_limpo = limpar_nome(nome)
    descricao = produto.get("descricao", "")            # descricao real -> conteudo fiel
    tipo = rotacao.tipo_carrossel()                      # intercala beneficios/curiosidades/modo
    print(f"Carrossel | tipo: {tipo} | produto: {nome}")

    frasco, sc = melhor_recorte(produto, lambda u: net.get(u, timeout=30).content, composer)
    if frasco is None:
        raise SystemExit("ERRO: nao consegui recortar nenhuma foto.")
    print(f"Foto escolhida (score {sc:.2f} - menor=mais limpo)")

    itens = gerar_itens(nome, tipo, _llm(), descricao=descricao)
    slides = montar_carrossel(tipo, nome_limpo, frasco, itens)
    print(f"{len(slides)} slides montados (capa + {len(itens)} + CTA)")

    gen = ImageGenerator()
    urls = []
    for i, s in enumerate(slides):
        buf = io.BytesIO(); s.save(buf, "PNG")
        urls.append(gen.hospedar(base64.b64encode(buf.getvalue()).decode()))
        print(f"slide {i+1}/{len(slides)} hospedado")

    # etiqueta de compra (Instagram Shopping) na capa e no slide final (os que tem o produto)
    tags = tags_para(nome, retailer_ids=ids_shopify(produto), com_posicao=True)
    tags_por_slide = {0: tags, len(urls) - 1: tags} if tags else None
    print("Etiqueta de produto:", "sim" if tags else "nao encontrada")

    legenda = legenda_carrossel(nome, tipo)
    media_id = publicar_carrossel(urls, legenda, tags_por_slide)
    historico.registrar(f"Carrossel ({tipo})", nome, media_id, tipo.upper())
    print(f"OK -> carrossel publicado | tipo: {tipo} | produto: {nome} | id: {media_id}")


if __name__ == "__main__":
    main()
