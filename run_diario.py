# -*- coding: utf-8 -*-
"""
Ciclo diario do FEED (post unico).

Agora o feed usa os MESMOS geradores do story/reel/carrossel: le a DESCRICAO
REAL do produto, escolhe um angulo COSMETICO (cabelo OU pele, NUNCA saude) e
passa TODO texto pela trava de compliance (ANVISA). Resultado: o feed nunca
mais inventa uso, nunca chama de "óleo" o que nao e oleo, e nunca fala de
imunidade/saude. Publica UMA foto no feed, com etiqueta de compra.
"""
import base64
import io
import json
import os
import re
import time
from datetime import datetime

import requests

from src import config
from src import util_net as net
from src import historico, rotacao, tempo
from src import produtos as cat
from src.image import composer
from src.image.generator import ImageGenerator
from src.image.arte_informativo import montar as montar_arte
from src.image.foto import melhor_recorte
from src.agents.textos_informativo import gerar_textos
from src.compliance import foco_cosmetico, garantir, suavizar
from src.carrossel_conteudo import _exibicao
from src.social_shopping import tags_para, ids_shopify
from src.facebook.publicador import publicar_no_facebook

API = "https://graph.facebook.com/v25.0"


def _llm():
    """Cliente de IA (Anthropic). Sem chave -> None (usa a reserva compliant)."""
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


def _volume(nome):
    m = re.search(r'(\d+)\s*(ml|g|kg|l)\b', nome or "", re.I)
    return f"{m.group(1)} {m.group(2)}" if m else "120 ml"


def _legenda_feed(nome_exib, beneficios3, descricao):
    """Legenda do feed: nome correto + descricao suavizada + beneficios + CTA.
    Tudo passa pela trava de compliance (nunca claim de saude)."""
    desc = suavizar(descricao or "")[:170].strip()
    linhas = "\n".join(f"✓ {b}" for b in (beneficios3 or [])[:3])
    corpo = f"{nome_exib} 🌿\n\n"
    if desc:
        corpo += desc + "\n\n"
    if linhas:
        corpo += linhas + "\n\n"
    corpo += "🌿 100% natural • prensado a frio\n\n🛍️ Garanta o seu pelo link na bio — enviamos pra todo o Brasil!"
    fallback = f"{nome_exib} 🌿 Produto natural da EikoVida. Link na bio."
    tag = "#eikovida #oleosnaturais #belezanatural #cuidadonatural #cosmeticosnaturais #peleecabelo"
    return garantir(corpo, fallback) + "\n\n" + tag


def _modo_do_dia():
    """Terca e quinta = post de CONVERSAO (vende direto); demais dias = educativo.
    Bate com os horarios do diario.yml (Ter/Qui ~19h BRT marcado 'conversao')."""
    return "conversao" if tempo.agora().weekday() in (1, 3) else "educativo"


def _legenda_conversao(nome_exib, beneficios3, descricao, preco=""):
    """Legenda focada em VENDA: gatilho de oferta, frete pra todo Brasil e CTA
    forte de compra. Continua 100% dentro da trava de compliance (sem claim de saude)."""
    desc = suavizar(descricao or "")[:130].strip()
    linhas = "\n".join(f"✓ {b}" for b in (beneficios3 or [])[:3])
    preco_txt = ""
    try:
        if preco and float(str(preco).replace(",", ".")) > 0:
            preco_txt = f"\n\n💰 A partir de R$ {str(preco).replace('.', ',')}"
    except Exception:
        preco_txt = ""
    corpo = f"✨ {nome_exib} ✨\n\n"
    if desc:
        corpo += desc + "\n\n"
    if linhas:
        corpo += linhas + "\n\n"
    corpo += "🌿 100% natural • prensado a frio" + preco_txt
    corpo += "\n\n🚚 Enviamos para todo o Brasil"
    corpo += "\n🛒 Garanta o seu agora pelo link na bio — toque em comprar!"
    fallback = f"✨ {nome_exib} ✨ Garanta o seu pelo link na bio. Enviamos para todo o Brasil! 🚚"
    tag = "#eikovida #oleosnaturais #belezanatural #cuidadonatural #ofertaeikovida #fretepratodobrasil"
    return garantir(corpo, fallback) + "\n\n" + tag


def publicar_feed(image_url, caption, product_tags=None):
    """Publica UMA foto no feed (com etiqueta de compra). Se a etiqueta falhar,
    publica sem ela (nao perde o post)."""
    def _container(tags):
        p = {"image_url": image_url, "caption": caption, "access_token": config.PAGE_ACCESS_TOKEN}
        if tags:
            p["product_tags"] = json.dumps(tags)
        return net.post(f"{API}/{config.IG_ACCOUNT_ID}/media", params=p, timeout=60).json()

    cont = _container(product_tags)
    if "error" in cont and product_tags:
        print("aviso: etiqueta no feed falhou, publicando sem ela:", cont["error"].get("message"))
        cont = _container(None)
    if "error" in cont:
        raise RuntimeError(f"Container feed: {cont['error'].get('message')}")
    time.sleep(6)
    pub = net.post(f"{API}/{config.IG_ACCOUNT_ID}/media_publish",
                   params={"creation_id": cont["id"], "access_token": config.PAGE_ACCESS_TOKEN}, timeout=60).json()
    if "error" in pub:
        raise RuntimeError(f"Publish feed: {pub['error'].get('message')}")
    return pub.get("id")


def main():
    lista = cat.carregar()                          # products.json (com a descricao real)
    if not lista:
        raise SystemExit("ERRO: nenhum produto encontrado.")

    indice = rotacao.indice_produto("feed")
    produto = cat.escolher(lista, "feed", indice)   # nao repete o ingrediente (ex: 2x Coco)
    if not produto:
        raise SystemExit("ERRO: nenhum produto com imagem.")

    nome = produto.get("nome", "Produto")
    nome_exib = _exibicao(nome)                     # mantem o tipo (Óleo de.../Máscara...), sem volume/marca
    descricao = produto.get("descricao", "")
    tags_txt = " ".join(produto.get("tags", []) or [])
    foco = foco_cosmetico(nome, descricao, tags_txt)   # CABELO ou PELE, NUNCA saude
    print(f"Feed | produto: {nome} | foco: {foco}")

    frasco, sc = melhor_recorte(produto, lambda u: net.get(u, timeout=30).content, composer)
    if frasco is None:
        raise SystemExit("ERRO: nao consegui recortar nenhuma foto.")
    print(f"Foto escolhida (score {sc:.2f} - menor=mais limpo)")

    t = gerar_textos(nome_exib, descricao[:600], foco, _llm())   # estuda a descricao real
    arte = montar_arte(frasco, nome_exib, foco, t.get("tagline3", []),
                       t.get("descricao", ""), t.get("beneficios3", []),
                       volume=_volume(nome))

    buf = io.BytesIO(); arte.save(buf, "PNG")
    image_url = ImageGenerator().hospedar(base64.b64encode(buf.getvalue()).decode())
    print("Arte hospedada:", image_url)

    modo = _modo_do_dia()
    if modo == "conversao":
        legenda = _legenda_conversao(nome_exib, t.get("beneficios3", []), descricao, produto.get("preco", ""))
    else:
        legenda = _legenda_feed(nome_exib, t.get("beneficios3", []), descricao)
    print(f"Modo do dia: {modo}")
    tags = tags_para(nome, retailer_ids=ids_shopify(produto), com_posicao=True)
    print("Etiqueta de produto:", "sim" if tags else "nao encontrada")

    media_id = publicar_feed(image_url, legenda, tags)
    historico.registrar("Feed", nome, media_id, foco)
    print(f"OK -> feed publicado | produto: {nome} | foco: {foco} | id: {media_id}")

    # Espelha no Facebook. O Instagram e prioridade: se o FB falhar, o post do
    # Instagram ja esta publicado e o sistema apenas registra um aviso.
    try:
        fb_id = publicar_no_facebook(image_url, legenda, token=config.PAGE_ACCESS_TOKEN)
        print(f"OK -> espelhado no Facebook | id: {fb_id}")
    except Exception as e:
        print(f"aviso: falhou espelhar no Facebook (Instagram ja publicou): {e}")


if __name__ == "__main__":
    main()