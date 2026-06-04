"""
Agente de Legendas.
Gera legendas adaptadas a cada plataforma (Instagram, Facebook, TikTok),
usando a voz da marca recuperada do vault via RAG.
"""
from src.llm.client import LLMClient
from src.rag import search

# Instruções específicas por plataforma
ESTILO_PLATAFORMA = {
    "instagram": (
        "Instagram: tom visual e inspirador, emojis com elegância, "
        "quebra de linha para leitura fácil, pergunta no final para gerar comentários."
    ),
    "facebook": (
        "Facebook: tom um pouco mais explicativo e acolhedor, "
        "pode ser ligeiramente mais longo, foco em compartilhamento."
    ),
    "tiktok": (
        "TikTok: tom jovem e direto, gancho forte na primeira linha, "
        "linguagem descontraída, curto e dinâmico."
    ),
}

SYSTEM = (
    "Você é copywriter de redes sociais especialista na voz da marca. "
    "Escreve legendas autênticas que conectam com o público. "
    "Responda apenas com a legenda final, sem hashtags e sem comentários extras."
)


def gerar_legenda(ideia: str, plataforma: str, llm: LLMClient = None) -> str:
    """Gera uma legenda para a ideia, adaptada à plataforma."""
    plataforma = plataforma.lower()
    if plataforma not in ESTILO_PLATAFORMA:
        raise ValueError(f"Plataforma não suportada: {plataforma}")

    llm = llm or LLMClient()
    contexto = search.montar_contexto(ideia)

    prompt = (
        f"Ideia do post: {ideia}\n\n"
        f"Voz e contexto da marca:\n{contexto or '(sem contexto indexado)'}\n\n"
        f"Estilo da plataforma — {ESTILO_PLATAFORMA[plataforma]}\n\n"
        f"Escreva a legenda final."
    )
    return llm.gerar(prompt, system=SYSTEM, max_tokens=700)


def gerar_para_todas(ideia: str, plataformas: list[str], llm: LLMClient = None) -> dict:
    """Gera legendas para várias plataformas de uma vez."""
    return {p: gerar_legenda(ideia, p, llm) for p in plataformas}
