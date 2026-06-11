# -*- coding: utf-8 -*-
"""
Ciclo diario do FEED (post normal). Usa as credenciais do ambiente (GitHub Secrets).

CORRECAO DO PRODUTO REPETIDO:
Antes, o produto era escolhido por `tm_yday` (dia do ano) dentro do pipeline -> igual
o dia inteiro, e como o feed roda de manha E de noite, repetia o mesmo produto.
Agora o produto e escolhido aqui pela rotacao (varia por dia, horario e formato),
e entregue pronto ao pipeline via `produtos=[...]`. Assim manha != noite, e o feed
nao repete o produto do story/reel/carrossel.
"""
from src.pipeline import executar_diario
from src import catalogo, rotacao

# Imagem-base padrao (mantida do original).
PRODUTO_IMG = "https://eikovida.com/cdn/shop/files/criativos30ml_9.png"


def main():
    produtos = catalogo.carregar()
    escolhido = None
    if produtos:
        indice = rotacao.indice_produto("feed")     # varia por dia + horario
        escolhido = catalogo.escolher(produtos, indice)

    # Entrega a lista com 1 produto -> o pipeline publica exatamente esse.
    # (Se algo falhar, cai no comportamento antigo passando produtos=None.)
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
