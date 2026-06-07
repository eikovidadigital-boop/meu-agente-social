# -*- coding: utf-8 -*-
"""
TESTE do Story (sem publicar). Gera o story do produto do dia usando o
FRASCO REAL recortado e salva 'story_teste.png' para conferencia.
NAO publica nada. NAO gasta API (usa textos de reserva seguros).
"""
from datetime import datetime
import requests

from src import catalogo
from src.image import composer
from src.image.story_arte import montar_story
from src.agents.textos_informativo import gerar_textos
from src.compliance import focos_permitidos

try:
    from src.agents.arte_textos import escolher_foco
except Exception:
    def escolher_foco(indice, n):
        return ["PELE", "CABELO", "SAUDE"][(indice // max(n, 1)) % 3]


def _nome(produto):
    for k in ("nome", "titulo", "title"):
        if produto.get(k):
            return produto[k]
    return "Produto"


def _url_imagem(produto):
    # tenta varias formas de obter a melhor imagem do produto
    if produto.get("imagem"):
        return produto["imagem"]
    if hasattr(catalogo, "melhor_imagem"):
        try:
            u = catalogo.melhor_imagem(produto)
            if u:
                return u
        except Exception:
            pass
    imgs = produto.get("imagens") or produto.get("images") or []
    return imgs[0] if imgs else None


def main():
    produtos = catalogo.carregar()
    print(f"Produtos carregados: {len(produtos)}")
    if not produtos:
        raise SystemExit("ERRO: catalogo vazio (products.json nao carregou).")

    indice = datetime.now().timetuple().tm_yday

    # escolhe o produto do dia e garante que tem imagem (tenta os seguintes se faltar)
    produto = url = None
    n = len(produtos)
    for passo in range(n):
        cand = produtos[(indice + passo) % n]
        u = _url_imagem(cand)
        if u:
            produto, url = cand, u
            break
    if not produto:
        raise SystemExit("ERRO: nenhum produto com imagem encontrada.")

    nome = _nome(produto)
    foco = escolher_foco(indice, n)
    permitidos = focos_permitidos(nome)
    if foco not in permitidos:
        foco = permitidos[0]

    # FRASCO REAL recortado (usar_ia=False = rapido, sem baixar rembg)
    dados = requests.get(url, timeout=30).content
    frasco = composer.bbox_conteudo(composer.recortar_produto(dados, usar_ia=False))

    # textos de reserva seguros (sem chamar LLM); compliance ja embutido
    t = gerar_textos(nome, "", foco, None)

    montar_story(frasco, nome, foco, t["tagline3"]).save("story_teste.png")
    print(f"OK -> story_teste.png | produto: {nome} | foco: {foco}")


if __name__ == "__main__":
    main()
