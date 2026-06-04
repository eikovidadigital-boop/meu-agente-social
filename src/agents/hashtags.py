"""
Agente de Hashtags.
Gera hashtags relevantes para o tema e aplica rotação anti-repetição:
nunca devolve exatamente o mesmo conjunto duas vezes seguidas.
"""
import random

from src.llm.client import LLMClient

SYSTEM = (
    "Você gera hashtags para redes sociais. Responda apenas com as hashtags "
    "separadas por espaço, todas começando com #, sem texto extra."
)


def _parse_hashtags(texto: str) -> list[str]:
    tags = [t for t in texto.replace("\n", " ").split() if t.startswith("#")]
    # remove duplicatas preservando ordem
    vistas, unicas = set(), []
    for t in tags:
        tl = t.lower()
        if tl not in vistas:
            vistas.add(tl)
            unicas.append(t)
    return unicas


def gerar_hashtags(tema: str, n: int = 15, base: list[str] = None, llm: LLMClient = None) -> str:
    """
    Gera ~n hashtags para o tema. Mantém um conjunto base fixo (marca)
    e sorteia o restante de um pool maior para garantir variedade.
    """
    llm = llm or LLMClient()
    base = base or []

    prompt = (
        f"Tema: {tema}\n"
        f"Gere {n + 10} hashtags relevantes e variadas para esse tema em português, "
        f"misturando populares e de nicho."
    )
    resposta = llm.gerar(prompt, system=SYSTEM, max_tokens=300)
    pool = _parse_hashtags(resposta)

    # Remove as que já estão na base para não duplicar
    base_lower = {b.lower() for b in base}
    pool = [t for t in pool if t.lower() not in base_lower]

    # Rotação: sorteia do pool para nunca repetir o mesmo conjunto
    qtd_extra = max(0, n - len(base))
    extras = random.sample(pool, min(qtd_extra, len(pool))) if pool else []

    final = list(base) + extras
    random.shuffle(final)
    return " ".join(final)
