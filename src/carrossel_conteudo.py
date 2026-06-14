# -*- coding: utf-8 -*-
"""
Conteudo dos CARROSSEIS (beneficios, modo_usar, curiosidades), JA compliant
E FIEL AO PRODUTO.

Regra de ouro: o texto so pode falar do que esta na DESCRICAO OFICIAL do produto.
Nunca inventa uso, parte do corpo ou forma de aplicar. Assim um produto so de
cabelo (ex: condicionador) jamais vira "passe na pele".

- Com `llm` E descricao: gera conteudo fiel (IA), revisado pelas regras ANVISA.
- Sem descricao ou sem `llm`: usa a reserva SEGURA (generica, nao afirma onde usar).
"""
import json
import re

try:
    from src.compliance import revisar, suavizar, garantir, eh_sensivel
    from src.agents.textos_informativo import REGRAS, ANVISA
except ImportError:
    from compliance import revisar, suavizar, garantir, eh_sensivel
    from agents.textos_informativo import REGRAS, ANVISA

INSTR = {
    "beneficios":   "Liste 3 BENEFICIOS reais do produto, com base na descricao oficial. "
                    "Cada item: titulo de 2 a 3 palavras + 1 frase curta.",
    "modo_usar":    "Explique em 3 passos COMO USAR o produto, seguindo EXATAMENTE a forma de "
                    "uso que estiver na descricao oficial. Cada passo: titulo de 2 a 3 palavras "
                    "+ 1 frase curta.",
    "curiosidades": "Traga 3 CURIOSIDADES sobre o produto (origem, composicao, modo de producao), "
                    "com base na descricao oficial. Cada item: titulo de 2 a 3 palavras + 1 frase curta.",
}

# Reserva SEGURA (sem IA / sem descricao): generica e cosmetica, NUNCA afirma
# onde aplicar nem para que serve especificamente. Vale pra qualquer produto.
FALLBACK = {
    "beneficios": [
        ("100% natural", "Produto natural da EikoVida, feito com cuidado pra você."),
        ("Pureza", "Sem misturas desnecessárias — o melhor que a natureza oferece."),
        ("Cuidado natural", "Faz parte de uma rotina de cuidado mais natural."),
    ],
    "modo_usar": [
        ("Siga o rótulo", "Use conforme as instruções do rótulo do produto."),
        ("No seu ritmo", "Inclua na sua rotina de cuidado quando quiser."),
        ("Comece com pouco", "Comece com pouca quantidade e ajuste como preferir."),
    ],
    "curiosidades": [
        ("Da natureza", "Feito a partir de ingredientes de origem natural."),
        ("Feito com cuidado", "Produzido com atenção à qualidade pela EikoVida."),
        ("Linha natural", "Faz parte da linha de produtos naturais da EikoVida."),
    ],
}


def _exibicao(nome):
    """Nome pra exibir: tira volume e marca, mas MANTEM o tipo do produto
    (ex: 'Óleo de Coco', 'Condicionador Hidratante') — nunca forca 'Óleo de'."""
    n = re.sub(r'(?i)\b\d+\s*(ml|g|kg|l)\b', '', nome or "")
    n = re.sub(r'(?i)\beiko\s*vida\b|\beiko\b', '', n)
    n = re.sub(r'\s{2,}', ' ', n).strip(' -•,')
    return n or (nome or "").strip()


def _validar(itens, tipo):
    """Compliance em cada (titulo, texto). Descarta os ruins e completa com a reserva ate 3."""
    bons = []
    for it in (itens or [])[:5]:
        try:
            tit, tx = str(it[0]).strip(), str(it[1]).strip()
        except Exception:
            continue
        tit = tit if revisar(tit).ok else suavizar(tit)
        tx = tx if revisar(tx).ok else suavizar(tx)
        if tit and tx and revisar(tit).ok and revisar(tx).ok:
            bons.append((tit, tx))
    for fb in FALLBACK[tipo]:
        if len(bons) >= 3:
            break
        if fb not in bons:
            bons.append(fb)
    return bons[:3]


def gerar_itens(nome, tipo, llm=None, descricao=""):
    """[(titulo, texto) x3] compliant e FIEL. Usa a descricao oficial como unica fonte.
    Sem descricao ou sem llm -> reserva segura (nao inventa uso)."""
    tipo = tipo if tipo in INSTR else "beneficios"
    desc = (descricao or "").strip()

    # Sem como estudar o produto: reserva segura (jamais inventa onde aplicar)
    if llm is None or not desc:
        return list(FALLBACK[tipo])

    exib = _exibicao(nome)
    sensivel = eh_sensivel(nome) or eh_sensivel(desc)
    prompt = (
        f"Voce escreve conteudo curto para um CARROSSEL do Instagram da marca EikoVida.\n\n"
        f"PRODUTO: {exib}\n\n"
        f"DESCRICAO OFICIAL DO PRODUTO (sua UNICA fonte de informacao):\n"
        f'"""{desc}"""\n\n'
        f"{INSTR[tipo]}\n\n"
        f"REGRAS OBRIGATORIAS (nao quebre nenhuma):\n"
        f"1. Use SOMENTE o que esta na descricao oficial. E PROIBIDO inventar usos, "
        f"indicacoes, partes do corpo ou formas de aplicar que nao estejam la.\n"
        f"2. Respeite a finalidade: se a descricao indica uso no CABELO, fale apenas de "
        f"cabelo; se na PELE, apenas pele; se for de uso interno/outro, respeite. NUNCA "
        f"misture nem suponha onde usar.\n"
        f"3. Nao chame o produto de 'oleo' se ele nao for um oleo (confira no nome e na descricao).\n"
        f"4. Se a descricao nao disser como usar, oriente de forma generica e segura "
        f"('use conforme o rotulo'), sem inventar onde aplicar.\n"
        f"{REGRAS}" + (ANVISA if sensivel else "") +
        "\n\nResponda APENAS um JSON valido, sem texto extra, no formato:\n"
        '{"itens":[{"titulo":"...","texto":"..."},{"titulo":"...","texto":"..."},'
        '{"titulo":"...","texto":"..."}]}'
    )
    try:
        resp = llm.responder(prompt) if hasattr(llm, "responder") else llm(prompt)
        txt = resp.strip().replace("```json", "").replace("```", "").strip()
        data = json.loads(txt)
        itens = [(i.get("titulo", ""), i.get("texto", "")) for i in data.get("itens", [])]
    except Exception:
        itens = []
    return _validar(itens, tipo)


def legenda_carrossel(nome, tipo):
    """Legenda do carrossel: gancho por tipo + CTA (link na bio) + hashtags. Compliant."""
    exib = _exibicao(nome)
    gancho = {
        "beneficios":   f"Conheça os benefícios do {exib} 🌿",
        "modo_usar":    f"Aprenda a usar o {exib} do jeito certo 🌿",
        "curiosidades": f"Você sabia disso sobre o {exib}? 🌿",
    }.get(tipo, f"{exib} 🌿")
    tag = "#eikovida #oleosnaturais #belezanatural #cuidadonatural #cosmeticosnaturais #peleecabelo"
    corpo = (
        f"{gancho}\n\n"
        f"Arraste para o lado e descubra ➡️\n"
        f"100% puro e natural • prensado a frio\n\n"
        f"🛍️ Garanta o seu pelo link na bio — enviamos pra todo o Brasil!"
    )
    fallback = f"{exib} 🌿 Produto natural da EikoVida. Link na bio."
    return garantir(corpo, fallback) + "\n\n" + tag
