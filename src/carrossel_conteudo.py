# -*- coding: utf-8 -*-
"""
Conteudo dos CARROSSEIS (beneficios, modo_usar, curiosidades), JA compliant.
Mesmo padrao do projeto: recebe o objeto `llm` (dependency injection).
- Com `llm`: gera conteudo especifico do oleo (texto da IA), revisado pelas regras ANVISA.
- Sem `llm`: usa a reserva segura (conteudo cosmetico generico).
Tudo passa pelo guarda-palavras (compliance) antes de entrar no slide.
"""
import json

try:
    from src.compliance import revisar, suavizar, garantir, eh_sensivel
    from src.agents.textos_informativo import REGRAS, ANVISA
except ImportError:
    from compliance import revisar, suavizar, garantir, eh_sensivel
    from agents.textos_informativo import REGRAS, ANVISA

INSTR = {
    "beneficios":   "Liste 3 BENEFICIOS cosmeticos do oleo (cuidado da pele e dos fios). "
                    "Cada item: titulo de 2 a 3 palavras + 1 frase curta.",
    "modo_usar":    "Explique em 3 passos COMO USAR o oleo (na pele, no cabelo, na rotina de cuidado). "
                    "Cada passo: titulo de 2 a 3 palavras + 1 frase curta.",
    "curiosidades": "Traga 3 CURIOSIDADES sobre o oleo (origem, extracao prensada a frio, composicao natural). "
                    "Cada item: titulo de 2 a 3 palavras + 1 frase curta.",
}

# Reserva segura (sem IA). Conteudo cosmetico, sem nenhum claim de cura.
FALLBACK = {
    "beneficios": [
        ("Hidratação natural", "Ajuda a nutrir e hidratar, deixando a pele e os fios mais macios."),
        ("Toque leve", "Faz parte do cuidado diário, sem deixar sensação pesada."),
        ("Rico em nutrientes", "Óleo 100% puro, com o que a natureza oferece de melhor."),
    ],
    "modo_usar": [
        ("Na pele", "Aplique algumas gotas e massageie suavemente até a pele absorver."),
        ("No cabelo", "Espalhe nas pontas úmidas para nutrir e dar mais brilho aos fios."),
        ("Na rotina", "Use de manhã ou à noite, sempre que quiser cuidar de você."),
    ],
    "curiosidades": [
        ("Prensado a frio", "Esse método ajuda a preservar os nutrientes naturais do óleo."),
        ("100% puro", "Sem mistura e sem química: só o óleo vegetal natural."),
        ("Da natureza", "Extraído de fonte natural, do jeito mais tradicional."),
    ],
}


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


def gerar_itens(nome, tipo, llm=None):
    """Devolve [(titulo, texto), ...] (3 itens) ja compliant, pro carrossel do tipo dado."""
    tipo = tipo if tipo in INSTR else "beneficios"
    if llm is None:
        return list(FALLBACK[tipo])
    sensivel = eh_sensivel(nome)
    prompt = (
        f"Voce escreve conteudo curto para um CARROSSEL do Instagram da marca EikoVida "
        f"(oleos vegetais 100% puros). Produto: Óleo de {nome}.\n"
        f"{INSTR[tipo]}\n\n{REGRAS}" + (ANVISA if sensivel else "") +
        "\nResponda APENAS um JSON valido, sem texto extra, no formato:\n"
        '{"itens":[{"titulo":"...","texto":"..."},{"titulo":"...","texto":"..."},{"titulo":"...","texto":"..."}]}'
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
    gancho = {
        "beneficios":   f"Conheça os benefícios do Óleo de {nome} 🌿",
        "modo_usar":    f"Aprenda a usar o Óleo de {nome} do jeito certo 🌿",
        "curiosidades": f"Você sabia disso sobre o Óleo de {nome}? 🌿",
    }.get(tipo, f"Óleo de {nome} 🌿")
    tag = "#eikovida #oleosnaturais #belezanatural #cuidadonatural #cosmeticosnaturais #peleecabelo"
    corpo = (
        f"{gancho}\n\n"
        f"Arraste para o lado e descubra ➡️\n"
        f"100% puro e natural • prensado a frio\n\n"
        f"🛍️ Garanta o seu pelo link na bio — enviamos pra todo o Brasil!"
    )
    fallback = f"Óleo de {nome} 🌿 100% puro e natural. Link na bio."
    return garantir(corpo, fallback) + "\n\n" + tag
