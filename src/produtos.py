# -*- coding: utf-8 -*-
"""
Fonte unica e confiavel de produtos pro sistema.

Busca os produtos direto da loja (products.json), JA com a DESCRICAO REAL de
cada um (pra o conteudo nunca inventar uso) e escolhe o produto do post
EVITANDO repetir o mesmo ingrediente (ex: nao posta dois "Coco" seguidos).

Estado por formato fica em data/ultimo_<formato>.txt (o Ciclo Diario ja
commita a pasta data/, entao a memoria persiste entre execucoes).
"""
import os
import re
import unicodedata

try:
    from src import util_net as net
except ImportError:  # rodando fora do pacote (testes)
    import util_net as net

LOJA = "https://eikovida.com/products.json"
ESTADO_DIR = "data"


# ----------------------------------------------------------------------------- helpers
def _sem_acento(s):
    return "".join(c for c in unicodedata.normalize("NFD", s or "")
                   if unicodedata.category(c) != "Mn")


def _limpar_html(html):
    """Transforma o body_html do Shopify em texto limpo (pro prompt da IA)."""
    if not html:
        return ""
    txt = re.sub(r"(?is)<(script|style).*?</\1>", " ", html)
    txt = re.sub(r"<[^>]+>", " ", txt)            # tira tags
    txt = re.sub(r"&[a-z]+;", " ", txt)            # tira entidades (&nbsp; etc)
    txt = re.sub(r"\s+", " ", txt).strip()
    return txt[:1200]                              # limita tamanho pro prompt


def _ingrediente(nome):
    """Reduz ao nome essencial (sem 'Óleo de', volume e marca)."""
    n = nome or ""
    n = re.sub(r'(?i)^\s*[óo]leo\s+(vegetal\s+)?(de\s+|da\s+|do\s+)?', '', n)
    n = re.sub(r'(?i)\b\d+\s*(ml|g|kg|l)\b', '', n)
    n = re.sub(r'(?i)\beiko\s*vida\b|\beiko\b', '', n)
    n = re.sub(r'\s{2,}', ' ', n).strip(' -•,')
    return n or (nome or "").strip()


def familia(produto):
    """Ingrediente-base, pra agrupar variacoes do mesmo produto.
    'Óleo de Coco Spray', 'Óleo de Coco 120ml' e 'Coco Extra Virgem' -> 'coco'."""
    base = _ingrediente(produto.get("nome", "") if isinstance(produto, dict) else str(produto))
    partes = base.split()
    return _sem_acento(partes[0].lower()) if partes else "?"


# ----------------------------------------------------------------------------- carregar
def carregar(baixar_fn=None):
    """Lista de produtos normalizados, com a descricao real:
    {nome, imagem, imagens, descricao, tipo, tags, handle, variants}."""
    def _get_json(url):
        if baixar_fn:
            return baixar_fn(url)
        return net.get(url, timeout=30).json()

    produtos = []
    pagina = 1
    while pagina <= 20:
        try:
            data = _get_json(f"{LOJA}?limit=250&page={pagina}")
        except Exception as e:
            print("aviso: products.json falhou:", e)
            break
        lote = (data or {}).get("products") or []
        if not lote:
            break
        for p in lote:
            imgs = [i.get("src") for i in (p.get("images") or []) if isinstance(i, dict) and i.get("src")]
            tags = p.get("tags")
            if isinstance(tags, str):
                tags = [t.strip() for t in tags.split(",") if t.strip()]
            desc = _limpar_html(p.get("body_html"))
            info = desc[:200].strip() or (p.get("product_type") or "").strip() \
                or "Óleo vegetal 100% natural da EikoVida"
            produtos.append({
                "nome": (p.get("title") or "").strip(),
                "imagem": imgs[0] if imgs else "",
                "imagens": [{"src": s} for s in imgs],
                "descricao": desc,
                "info": info,                  # o pipeline do feed exige este campo
                "tipo": (p.get("product_type") or "").strip(),
                "tags": tags or [],
                "handle": p.get("handle", ""),
                "variants": p.get("variants") or [],
            })
        pagina += 1
    return produtos


# ----------------------------------------------------------------------------- memoria
def _arq(formato):
    return os.path.join(ESTADO_DIR, f"ultimo_{formato}.txt")


def _ultimas(formato, quantas=2):
    try:
        return open(_arq(formato), encoding="utf-8").read().split()[-quantas:]
    except Exception:
        return []


def _registrar(formato, fam):
    try:
        os.makedirs(ESTADO_DIR, exist_ok=True)
        try:
            hist = open(_arq(formato), encoding="utf-8").read().split()
        except Exception:
            hist = []
        hist.append(fam)
        open(_arq(formato), "w", encoding="utf-8").write(" ".join(hist[-10:]))
    except Exception:
        pass


# ----------------------------------------------------------------------------- escolher
def _tem_imagem(p):
    return bool(p.get("imagem") or p.get("imagens") or p.get("images"))


def escolher(produtos, formato, indice, evitar_repeticao=True):
    """Escolhe um produto pela rotacao (indice), PULANDO os que tem a mesma
    familia de ingrediente dos ultimos posts daquele formato e os sem imagem.
    Relaxa em catalogo pequeno: evita as 2 ultimas familias; se esgotar, evita
    so a ultima; so repete se houver uma unica familia. Registra a escolha."""
    validos = [p for p in (produtos or []) if _tem_imagem(p)]
    if not validos:
        return None
    n = len(validos)

    if evitar_repeticao:
        for qtd in (2, 1):                     # tenta nao repetir as 2 ultimas; senao, so a ultima
            evitar = set(_ultimas(formato, quantas=qtd))
            for passo in range(n):
                cand = validos[(indice + passo) % n]
                if familia(cand) not in evitar:
                    _registrar(formato, familia(cand))
                    return cand

    escolhido = validos[indice % n]            # catalogo com 1 unica familia: usa o do indice
    _registrar(formato, familia(escolhido))
    return escolhido
