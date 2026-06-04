"""
Agente de Ideias.
Gera ideias de conteúdo do dia, embasado no contexto recuperado do vault
(estratégia, produtos, mercado) via RAG.
"""
from src.llm.client import LLMClient
from src.rag import search

SYSTEM = (
    "Você é estrategista de conteúdo para redes sociais. "
    "Gera ideias práticas, alinhadas à marca e ao público, que geram engajamento. "
    "Responda apenas com as ideias, uma por linha, sem numeração ou texto extra."
)


def gerar_ideias(objetivo: str, n: int = 3, llm: LLMClient = None) -> list[str]:
    """Gera N ideias de conteúdo para o objetivo informado."""
    llm = llm or LLMClient()
    contexto = search.montar_contexto(objetivo)

    prompt = (
        f"Objetivo: {objetivo}\n\n"
        f"Contexto da marca (use como base):\n{contexto or '(sem contexto indexado)'}\n\n"
        f"Gere {n} ideias de conteúdo distintas e específicas, uma por linha."
    )
    resposta = llm.gerar(prompt, system=SYSTEM, max_tokens=500)

    ideias = [linha.strip(" -•\t") for linha in resposta.splitlines() if linha.strip()]
    return ideias[:n]
