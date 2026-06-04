"""
Busca semântica do RAG.
Recebe uma pergunta/tarefa e retorna apenas os trechos mais relevantes
do vault — nunca o vault inteiro. É isso que mantém o consumo de tokens baixo.
"""
import chromadb

from src import config
from src.rag.embeddings import get_embedding_function


def buscar(consulta: str, top_k: int = None) -> list[dict]:
    """
    Busca os trechos mais relevantes para a consulta.
    Retorna lista de dicts: {texto, nota, score}.
    """
    top_k = top_k or config.BUSCA_TOP_K
    cliente = chromadb.PersistentClient(path=str(config.CHROMA_DIR))
    try:
        colecao = cliente.get_collection(
            name="vault", embedding_function=get_embedding_function()
        )
    except Exception:
        return []  # índice ainda não existe

    total = colecao.count()
    if total == 0:
        return []

    resultado = colecao.query(query_texts=[consulta], n_results=min(top_k, total))

    trechos = []
    docs = resultado.get("documents", [[]])[0]
    metas = resultado.get("metadatas", [[]])[0]
    distancias = resultado.get("distances", [[]])[0]
    for texto, meta, dist in zip(docs, metas, distancias):
        trechos.append({
            "texto": texto,
            "nota": meta.get("nota", "?"),
            "score": round(1 - dist, 3),  # quanto maior, mais relevante
        })
    return trechos


def montar_contexto(consulta: str, top_k: int = None) -> str:
    """
    Monta um bloco de contexto enxuto com os trechos relevantes,
    pronto para injetar no prompt do Claude.
    """
    trechos = buscar(consulta, top_k)
    if not trechos:
        return ""
    partes = [f"[{t['nota']}]\n{t['texto']}" for t in trechos]
    return "\n\n---\n\n".join(partes)
