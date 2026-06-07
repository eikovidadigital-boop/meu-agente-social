# -*- coding: utf-8 -*-
"""
TESTE do Story (sem publicar). Gera o story do produto do dia usando o
FRASCO REAL recortado e salva 'story_teste.png' para conferencia.
Roda no GitHub Actions (workflow "Testar Story") ou local.
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


def main():
    produtos = catalogo.carregar()
    indice = datetime.now().timetuple().tm_yday
    produto = catalogo.escolher(produtos, indice)
    nome = produto["nome"]

    # foco do dia, respeitando produtos sensiveis (copaiba/sucupira/andiroba nunca SAUDE)
    foco = escolher_foco(indice, len(produtos))
    permitidos = focos_permitidos(nome)
    if foco not in permitidos:
        foco = permitidos[0]

    # FRASCO REAL recortado (usar_ia=False = rapido, sem baixar rembg)
    dados = requests.get(produto["imagem"], timeout=30).content
    frasco = composer.bbox_conteudo(composer.recortar_produto(dados, usar_ia=False))

    # textos de reserva seguros (sem chamar LLM); compliance ja embutido
    t = gerar_textos(nome, "", foco, None)

    story = montar_story(frasco, nome, foco, t["tagline3"])
    story.save("story_teste.png")
    print(f"OK -> story_teste.png | produto: {nome} | foco: {foco}")


if __name__ == "__main__":
    main()
