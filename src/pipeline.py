"""
Pipeline diário — amarra todos os módulos no fluxo automático.
Indexa o vault, escolhe um produto real do catálogo, MONTA a imagem
(produto real recortado + cenário gerado por IA, com layout que rotaciona),
gera legenda e hashtags, salva, agenda e publica.
O produto nunca é alterado pela IA. Dependências injetáveis para teste.
"""
import base64
from datetime import datetime

import requests

from src import catalogo
from src.agents import arte_textos, captions, hashtags, ideas
from src.image.generator import ImageGenerator
from src.rag import indexer
from src.social.facebook import FacebookPublisher
from src.social.instagram import InstagramPublisher
from src.social.publisher import Publisher
from src.storage import db


def objetivo_do_dia() -> str:
    """Educativo em Seg/Qua/Sex; conversão em Ter/Qui."""
    dia = datetime.now().weekday()  # 0=Seg ... 4=Sex
    if dia in (0, 2, 4):
        return "Conteúdo educativo que ensina algo útil e gera salvamentos"
    return "Conteúdo de conversão que apresenta um produto e gera vendas"


def _baixar(url: str) -> bytes:
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    return r.content


def executar_diario(objetivo=None, plataformas=("instagram", "facebook"),
                    produto_img_url=None, base_hashtags=None,
                    llm=None, image_gen=None, publisher=None, indexar=True,
                    produtos=None, baixar_fn=None) -> dict:
    """
    Executa o ciclo diário completo, montando a imagem (produto real + cenário IA).
    """
    objetivo = objetivo or objetivo_do_dia()
    base_hashtags = base_hashtags or ["#eikovida"]
    baixar_fn = baixar_fn or _baixar
    image_gen = image_gen or ImageGenerator()

    db.init_db()
    if indexar:
        indexer.indexar_vault()

    # 1) Produto real do catálogo (rotaciona por dia)
    if produtos is None:
        try:
            produtos = catalogo.carregar_do_shopify()   # puxa do Shopify automaticamente
        except Exception:
            produtos = []
        if not produtos:
            produtos = catalogo.carregar()               # reserva: arquivo manual
    indice = datetime.now().timetuple().tm_yday
    produto = catalogo.escolher(produtos, indice)

    if produto:
        produto_url = produto["imagem"]
        contexto_produto = f"Produto em foco: {produto['nome']}. {produto['info']}"
    else:
        produto_url = produto_img_url
        contexto_produto = ""

    # 2) Monta a imagem: produto real recortado + cenário IA + arte (título, selo, logo)
    #    escolhe automaticamente a foto mais limpa do produto (evita splash branco)
    if produto:
        produto_bytes = catalogo.melhor_imagem(produto, baixar_fn)
    else:
        produto_bytes = baixar_fn(produto_url)
    nome_prod = produto["nome"] if produto else "Óleo Natural"
    info_prod = produto["info"] if produto else ""
    textos_arte = arte_textos.gerar_textos(nome_prod, info_prod, llm=llm)
    imagem_url = image_gen.montar_com_cenario(produto_bytes, textos=textos_arte, indice=indice)

    # 3) Ideia do dia, focada no produto
    obj = f"{objetivo} {contexto_produto}".strip()
    lista = ideas.gerar_ideias(obj, n=1, llm=llm)
    ideia = lista[0] if lista else obj

    # 4) Conteúdo por plataforma (mesma imagem montada)
    conteudos = []
    for plataforma in plataformas:
        legenda = captions.gerar_legenda(ideia, plataforma, llm=llm)
        tags = hashtags.gerar_hashtags(ideia, base=base_hashtags, llm=llm)
        cid = db.salvar_conteudo(
            plataforma=plataforma, ideia=ideia, legenda=legenda,
            hashtags=tags, prompt_imagem="", imagem_url=imagem_url, status="pronto",
        )
        db.agendar_publicacao(cid, plataforma)
        conteudos.append(cid)

    # 5) Publica os pendentes
    publisher = publisher or Publisher([InstagramPublisher(), FacebookPublisher()])
    resultados = publisher.publicar_pendentes()

    return {
        "objetivo": objetivo,
        "produto": produto["nome"] if produto else None,
        "ideia": ideia,
        "imagem_url": imagem_url,
        "conteudos": conteudos,
        "publicacoes": resultados,
    }
