# -*- coding: utf-8 -*-
"""
Agente que gera os textos do LAYOUT 2 (informativo), por FOCO, JA compliant.
Padrao do projeto: dependency injection (recebe o objeto `llm`).

Saida: dict com nome, tagline3 (3 palavras), descricao (1 frase), beneficios3.
Toda saida passa pelo guarda-palavras (compliance) antes de retornar.
Foco SAUDE fala SO de composicao + uso culinario (nunca efeito em doenca).
"""
import json
try:
    from src.compliance import revisar, suavizar, eh_sensivel, focos_permitidos
except ImportError:
    from compliance import revisar, suavizar, eh_sensivel, focos_permitidos

# Instrucao extra para produtos fiscalizados pela ANVISA (copaiba, sucupira, andiroba)
ANVISA = (
    "\nATENCAO ESPECIAL (produto fiscalizado pela ANVISA):\n"
    "- PROIBIDO qualquer efeito terapeutico: anti-inflamatorio, cicatrizante, antisseptico,\n"
    "  analgesico, para dores/articulacoes/reumatismo, repelente, antimicrobiano.\n"
    "- Falar SOMENTE de hidratacao/cuidado cosmetico da pele ou dos fios e da composicao.\n"
)

REGRAS = (
    "REGRAS OBRIGATORIAS (Meta e Google Ads):\n"
    "- NUNCA dizer que cura, trata ou previne doenca/condicao.\n"
    "- NUNCA usar 2a pessoa diagnostica ('voce tem', 'voce sofre de', 'cansado de').\n"
    "- NUNCA usar 'garantido', 'comprovado', 'clinicamente', 'milagre', 'recomendado por medicos'.\n"
    "- Linguagem suave: 'ajuda a', 'faz parte do cuidado', 'indicado para'.\n"
    "- Se foco=SAUDE: falar SO de composicao (omega, vitaminas) e uso culinario. Nunca efeito em orgao/doenca.\n"
    "- Reforcar que o oleo e 100% puro e natural.\n"
)
ANGULO = {
    "PELE":   "cuidado e hidratacao da pele (beleza). Nao citar cabelo, saude ou culinaria.",
    "CABELO": "cuidado dos fios e do couro cabeludo (beleza). Nao citar pele, saude ou culinaria.",
    "SAUDE":  "valor nutricional (composicao) e uso na culinaria. Nao citar pele nem cabelo.",
}

FALLBACK = {
    "PELE":   dict(tagline3=["Nutre","Hidrata","Cuida"],
                   descricao="Óleo 100% puro para o cuidado diário da pele.",
                   beneficios3=["Hidratação profunda e duradoura","Maciez sem sensação oleosa","Rico em nutrientes naturais"]),
    "CABELO": dict(tagline3=["Nutre","Fortalece","Brilho"],
                   descricao="Óleo 100% puro para o cuidado dos fios.",
                   beneficios3=["Nutre os fios e as pontas","Ajuda a dar brilho e maciez","Faz parte da sua rotina capilar"]),
    "SAUDE":  dict(tagline3=["Puro","Nutritivo","Versátil"],
                   descricao="Óleo 100% puro prensado a frio, fonte natural de nutrientes.",
                   beneficios3=["Fonte natural de gorduras boas","Sabor leve para finalizar pratos","Ideal para saladas e receitas frias"]),
}

def _limpar(campos: dict, foco: str) -> dict:
    """Roda compliance em todos os textos. Se grave demais, cai no fallback do foco."""
    fb = FALLBACK[foco]
    out = {"tagline3": [], "descricao": "", "beneficios3": []}
    # tagline -> mantem as limpas e completa com fallback ate 3
    limpas = [p for p in campos.get("tagline3", [])[:3] if revisar(p).ok]
    for p in fb["tagline3"]:
        if len(limpas) >= 3: break
        if p not in limpas: limpas.append(p)
    out["tagline3"] = limpas[:3]
    # descricao
    d = campos.get("descricao", "")
    d = d if revisar(d).ok else suavizar(d)
    out["descricao"] = d if revisar(d).ok else fb["descricao"]
    # beneficios
    bens = []
    for b in campos.get("beneficios3", [])[:3]:
        b2 = b if revisar(b).ok else suavizar(b)
        bens.append(b2 if revisar(b2).ok else None)
    bens = [b for b in bens if b][:3]
    out["beneficios3"] = bens if len(bens) == 3 else fb["beneficios3"]
    return out

def gerar_textos(nome: str, info: str, foco: str, llm) -> dict:
    foco = (foco or "PELE").upper()
    sensivel = eh_sensivel(nome)
    # produto fiscalizado nunca usa foco SAUDE -> vira cosmetico (PELE)
    if sensivel and foco not in focos_permitidos(nome):
        foco = "PELE"
    prompt = (
        f"Voce escreve textos curtos para um post da marca EikoVida (oleos vegetais 100% puros).\n"
        f"Produto: {nome}. Info: {info}\n"
        f"FOCO deste post: {foco} -> {ANGULO.get(foco,'')}\n\n{REGRAS}"
        + (ANVISA if sensivel else "") +
        "\nResponda APENAS um JSON valido, sem texto extra, no formato:\n"
        '{"tagline3":["palavra1","palavra2","palavra3"],'
        '"descricao":"uma frase curta","beneficios3":["b1 curto","b2 curto","b3 curto"]}'
    )
    try:
        resp = llm.responder(prompt) if hasattr(llm, "responder") else llm(prompt)
        txt = resp.strip().replace("```json", "").replace("```", "").strip()
        campos = json.loads(txt)
    except Exception:
        campos = {}
    limpos = _limpar(campos, foco)
    limpos["nome"] = nome
    return limpos


def gerar_textos_kit(nome_kit: str, itens: list, llm=None) -> dict:
    """Textos do KIT (layout 3). Sempre cosmetico/combo, sem claim de saude.
    Se qualquer item do kit for sensivel (copaiba/sucupira/andiroba), mantem 100% cosmetico."""
    sensivel = any(eh_sensivel(i) for i in (itens or []))
    base = dict(
        tagline3=["Ritual", "Completo", "Natural"],
        descricao=f"{len(itens)} óleos 100% puros para o seu ritual de cuidado.",
    )
    if llm is not None:
        prompt = (
            f"Escreva textos curtos para um KIT da EikoVida chamado '{nome_kit}', com os óleos: {', '.join(itens)}.\n"
            f"{REGRAS}"
            + (ANVISA if sensivel else "") +
            "Foque em 'combo/ritual de cuidado/presente'. Nada de efeito terapeutico.\n"
            'Responda APENAS JSON: {"tagline3":["a","b","c"],"descricao":"uma frase"}'
        )
        try:
            import json as _json
            resp = llm.responder(prompt) if hasattr(llm, "responder") else llm(prompt)
            c = _json.loads(resp.strip().replace("```json","").replace("```","").strip())
            tg = [p for p in c.get("tagline3", [])[:3] if revisar(p).ok]
            for p in base["tagline3"]:
                if len(tg) >= 3: break
                if p not in tg: tg.append(p)
            base["tagline3"] = tg[:3]
            base["descricao"] = garantir(c.get("descricao",""), base["descricao"])
        except Exception:
            pass
    base["nome"] = nome_kit
    return base
