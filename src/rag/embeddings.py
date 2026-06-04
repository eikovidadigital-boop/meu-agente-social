"""
Funções de embedding plugáveis para o RAG.

Três opções (escolhidas por variável de ambiente RAG_EMBEDDING):
- "local"  : modelo ONNX nativo do ChromaDB (gratuito, roda offline após baixar o modelo). PADRÃO.
- "openai" : API de embeddings da OpenAI (custo ínfimo, sem download, rápido).
- "simple" : embedding bag-of-words por hashing (gratuito, sem dependências/download).
             Usado em testes e como fallback quando não há rede para baixar modelo.

Design plugável: trocar o motor não exige mudar o indexer nem a busca.
"""
import math
import os
import re

from chromadb.utils import embedding_functions


class SimpleHashingEmbeddingFunction:
    """
    Embedding leve baseado em bag-of-words com hashing.
    Não precisa de modelo nem internet. Captura sobreposição de palavras,
    suficiente para validar o pipeline e ranquear por relevância lexical.
    """
    def __init__(self, dim: int = 256):
        self.dim = dim

    def name(self) -> str:
        return "simple-hashing"

    def __call__(self, input):
        vetores = []
        for texto in input:
            vetor = [0.0] * self.dim
            palavras = re.findall(r"\w+", texto.lower())
            for palavra in palavras:
                idx = hash(palavra) % self.dim
                vetor[idx] += 1.0
            norma = math.sqrt(sum(v * v for v in vetor)) or 1.0
            vetores.append([v / norma for v in vetor])
        return vetores

    # Métodos exigidos por versões recentes do ChromaDB
    def embed_documents(self, input):
        return self(input)

    def embed_query(self, input):
        textos = input if isinstance(input, list) else [input]
        return self(textos)


def get_embedding_function(modo: str = None):
    """Retorna a função de embedding conforme o modo configurado."""
    modo = modo or os.environ.get("RAG_EMBEDDING", "local")

    if modo == "simple":
        return SimpleHashingEmbeddingFunction()

    if modo == "openai":
        return embedding_functions.OpenAIEmbeddingFunction(
            api_key=os.environ.get("OPENAI_API_KEY", ""),
            model_name="text-embedding-3-small",
        )

    # padrão: modelo local gratuito do ChromaDB
    return embedding_functions.DefaultEmbeddingFunction()
