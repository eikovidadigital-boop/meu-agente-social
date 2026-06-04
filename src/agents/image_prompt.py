"""
Agente de Prompt de Imagem.
Gera o prompt (em inglês) para o gerador de imagem, mantendo a identidade
visual da marca recuperada do vault via RAG.
"""
from src.llm.client import LLMClient
from src.rag import search

SYSTEM = (
    "You create concise English prompts for an AI image generator. "
    "Output only the prompt, no explanations. Keep it under 120 words."
)


def gerar_prompt_imagem(ideia: str, paleta: str = "", llm: LLMClient = None) -> str:
    """Gera um prompt de imagem para a ideia, com a identidade visual da marca."""
    llm = llm or LLMClient()
    contexto = search.montar_contexto(f"identidade visual marca {ideia}")

    prompt = (
        f"Post idea: {ideia}\n"
        f"Brand visual context: {contexto or '(none)'}\n"
        f"Brand palette: {paleta or '(use brand context)'}\n\n"
        f"Write an English image-generation prompt for a professional, "
        f"on-brand Instagram thumbnail. Square 1:1, consistent brand look."
    )
    return llm.gerar(prompt, system=SYSTEM, max_tokens=300)
