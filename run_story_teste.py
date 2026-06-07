# -*- coding: utf-8 -*-
"""
TESTE do Story (sem publicar). Gera o story do produto do dia com o FRASCO
REAL recortado e salva 'story_teste.png'. NAO publica. NAO gasta API.
Busca produtos via catalogo.carregar(); se vier vazio, le eikovida.com/products.json direto.
"""
from datetime import datetime
import requests

from src.image import composer
from src.image.story_arte import montar_story
from src.agents.textos_informativo import gerar_textos
from src.compliance import focos_permitidos
from src.image.foto import melhor_recorte, urls_produto

try:
    from src.agents.arte_textos import escolher_foco
except Exception:
    def escolher_foco(indice, n):
        return ["PELE", "CABELO", "SAUDE"][(indice // max(n, 1)) % 3]


def _carregar_catalogo():
    # 1) tenta a funcao do projeto
    try:
        from src import catalogo
        prods = catalogo.carregar()
        if prods:
            return prods, "catalogo.carregar()"
    except Exception as e:
        print("aviso: catalogo.carregar falhou:", e)
    # 2) fallback: products.json publico do Shopify (paginado)
    out, page = [], 1
    while page <= 10:
        r = requests.get(f"https://eikovida.com/products.json?limit=250&page={page}", timeout=30)
        data = r.json().get("products", [])
        if not data:
            break
        out += data
        page += 1
    return out, "products.json"


def _nome(p):
    for k in ("nome", "titulo", "title"):
        if p.get(k):
            return p[k]
    return "Produto"


def _url_imagem(p):
    if p.get("imagem"):
        return p["imagem"]
    for k in ("imagens", "images"):
        arr = p.get(k) or []
        if arr:
            primeiro = arr[0]
            if isinstance(primeiro, dict):              # products.json: {"src": ...}
                return primeiro.get("src") or primeiro.get("url")
            return primeiro                              # lista de strings
    return None


def main():
    produtos, fonte = _carregar_catalogo()
    print(f"Produtos carregados: {len(produtos)} (fonte: {fonte})")
    if not produtos:
        raise SystemExit("ERRO: nenhum produto encontrado.")

    indice = datetime.now().timetuple().tm_yday
    n = len(produtos)
    produto = None
    for passo in range(n):
        cand = produtos[(indice + passo) % n]
        if urls_produto(cand):
            produto = cand
            break
    if not produto:
        raise SystemExit("ERRO: nenhum produto com imagem.")

    nome = _nome(produto)
    foco = escolher_foco(indice, n)
    permitidos = focos_permitidos(nome)
    if foco not in permitidos:
        foco = permitidos[0]

    # escolhe a FOTO MAIS LIMPA do produto (sem splash), igual ao feed
    frasco, sc = melhor_recorte(produto, lambda u: requests.get(u, timeout=30).content, composer)
    if frasco is None:
        raise SystemExit("ERRO: nao consegui recortar nenhuma foto.")
    print(f"Foto escolhida (score {sc:.2f})")
    t = gerar_textos(nome, "", foco, None)
    montar_story(frasco, nome, foco, t["tagline3"]).save("story_teste.png")
    print(f"OK -> story_teste.png | produto: {nome} | foco: {foco}")


if __name__ == "__main__":
    main()
