"""
Pipeline diário — amarra todos os módulos no fluxo automático.
Indexa o vault, gera o conteúdo (ideia, legenda, hashtags, imagem),
salva, agenda e publica. Dependências injetáveis para teste.
"""
from datetime import datetime

from src.agents import captions, hashtags, ideas, image_prompt
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


def executar_diario(objetivo=None, plataformas=("instagram", "facebook"),
                    produto_img_url=None, base_hashtags=None,
                    llm=None, image_gen=None, publisher=None, indexar=True) -> dict:
    """
    Executa o ciclo diário completo.
    Retorna um resumo do que foi gerado e publicado.
    """
    objetivo = objetivo or objetivo_do_dia()
    base_hashtags = base_hashtags or ["#eikovida"]

    db.init_db()
    if indexar:
        indexer.indexar_vault()

    # 1) Ideia do dia
    lista = ideas.gerar_ideias(objetivo, n=1, llm=llm)
    ideia = lista[0] if lista else objetivo

    # 2) Imagem (uma só, reaproveitada nas plataformas — feed coeso)
    prompt = image_prompt.gerar_prompt_imagem(ideia, llm=llm)
    image_gen = image_gen or ImageGenerator()
    imagem_url = image_gen.criar(prompt, produto_img_url)

    # 3) Conteúdo por plataforma
    conteudos = []
    for plataforma in plataformas:
        legenda = captions.gerar_legenda(ideia, plataforma, llm=llm)
        tags = hashtags.gerar_hashtags(ideia, base=base_hashtags, llm=llm)
        cid = db.salvar_conteudo(
            plataforma=plataforma, ideia=ideia, legenda=legenda,
            hashtags=tags, prompt_imagem=prompt, imagem_url=imagem_url, status="pronto",
        )
        db.agendar_publicacao(cid, plataforma)
        conteudos.append(cid)

    # 4) Publica os pendentes
    publisher = publisher or Publisher([InstagramPublisher(), FacebookPublisher()])
    resultados = publisher.publicar_pendentes()

    return {
        "objetivo": objetivo,
        "ideia": ideia,
        "imagem_url": imagem_url,
        "conteudos": conteudos,
        "publicacoes": resultados,
    }
