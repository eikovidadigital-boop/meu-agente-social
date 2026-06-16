# -*- coding: utf-8 -*-
"""
Ciclo diario do FEED (post normal). Usa as credenciais do ambiente (GitHub Secrets).

Faz duas coisas alem de chamar o pipeline:
1) PRODUTO NAO REPETE: escolhe o produto pela rotacao (varia por dia + horario) e
   entrega pronto ao pipeline (manha != noite; nao repete story/reel/carrossel).
2) ETIQUETA DE COMPRA NO FEED: como o pipeline publica sem etiqueta, interceptamos
   o InstagramPublisher.publicar e injetamos a etiqueta do produto do dia
   (Instagram Shopping). Se nao houver catalogo/permissao, publica sem etiqueta.
"""
from src.pipeline import executar_diario
from src import produtos as cat, rotacao
from src.social.instagram import InstagramPublisher
from src.social_shopping import tags_para, ids_shopify

PRODUTO_IMG = "https://eikovida.com/cdn/shop/files/criativos30ml_9.png"


def _ligar_etiqueta(produto):
    """Faz o publicar do feed sempre incluir a etiqueta do produto do dia."""
    tags = tags_para(produto.get("nome", "") if isinstance(produto, dict) else getattr(produto, "nome", ""),
                     retailer_ids=ids_shopify(produto), com_posicao=True)
    if not tags:
        print("Etiqueta de produto no feed: nao encontrada (produto fora do catalogo Shopping?)")
        return
    _orig = InstagramPublisher.publicar

    def _com_tag(self, image_url, legenda, hashtags="", product_tags=None):
        return _orig(self, image_url, legenda, hashtags, product_tags=product_tags or tags)

    InstagramPublisher.publicar = _com_tag
    print("Etiqueta de produto no feed: sim")


def _blindar_pipeline():
    """No GitHub Actions o catalogo nativo volta vazio e o melhor_imagem dele nao
    aceita o formato vindo do products.json. Como o produto JA foi escolhido aqui,
    fazemos o pipeline: (1) usar exatamente esse produto e (2) baixar a imagem de
    forma robusta, aceitando qualquer formato de URL (string, dict ou lista)."""
    from src import catalogo
    from src.image.foto import urls_produto
    catalogo.escolher = lambda produtos, indice: (produtos[0] if produtos else None)

    def _melhor_imagem(produto, baixar_fn):
        urls = urls_produto(produto)
        return baixar_fn(urls[0]) if urls else None
    catalogo.melhor_imagem = _melhor_imagem


def main():
    _blindar_pipeline()
    lista = cat.carregar()                          # products.json (confiavel no Actions)
    escolhido = None
    if lista:
        indice = rotacao.indice_produto("feed")     # varia por dia + horario
        escolhido = cat.escolher(lista, "feed", indice)   # nao repete o ingrediente (ex: 2x Coco)

    if escolhido:
        _ligar_etiqueta(escolhido)

    resumo = executar_diario(
        produto_img_url=PRODUTO_IMG,
        produtos=[escolhido] if escolhido else None,
    )

    print("Resumo do ciclo diario:")
    for k in ("objetivo", "ideia", "imagem_url", "conteudos", "publicacoes"):
        if isinstance(resumo, dict) and k in resumo:
            print(f"  {k}: {resumo[k]}")


if __name__ == "__main__":
    main()
