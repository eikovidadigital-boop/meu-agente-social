"""
Indexador do RAG.
Lê as notas do vault (.md), divide em chunks e armazena no ChromaDB
com embeddings locais (gratuitos, sem API).

Indexação INCREMENTAL: cada nota tem um hash do conteúdo. Só notas novas
ou alteradas são reprocessadas — o vault inteiro nunca é reindexado à toa.
"""
import hashlib
from pathlib import Path

import chromadb

from src import config
from src.rag.embeddings import get_embedding_function


def _hash_conteudo(texto: str) -> str:
    """Gera hash do conteúdo para detectar mudanças."""
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()


def _dividir_em_chunks(texto: str, tamanho: int, sobreposicao: int):
    """Divide um texto em pedaços de ~tamanho palavras, com sobreposição."""
    palavras = texto.split()
    if not palavras:
        return []
    chunks = []
    passo = max(1, tamanho - sobreposicao)
    for inicio in range(0, len(palavras), passo):
        pedaco = palavras[inicio:inicio + tamanho]
        if pedaco:
            chunks.append(" ".join(pedaco))
        if inicio + tamanho >= len(palavras):
            break
    return chunks


def _colecao():
    """Abre (ou cria) a coleção do ChromaDB com a função de embedding configurada."""
    cliente = chromadb.PersistentClient(path=str(config.CHROMA_DIR))
    return cliente.get_or_create_collection(
        name="vault", embedding_function=get_embedding_function()
    )


def indexar_vault(vault_dir: Path = None) -> dict:
    """
    Indexa todas as notas .md do vault de forma incremental.
    Retorna um resumo: quantas notas foram processadas, puladas e removidas.
    """
    vault_dir = Path(vault_dir or config.VAULT_DIR)
    colecao = _colecao()

    # Mapa de hashes já indexados (por nota)
    existentes = colecao.get(include=["metadatas"])
    hash_por_nota = {}
    for meta in existentes["metadatas"] or []:
        hash_por_nota[meta["nota"]] = meta["hash"]

    notas_no_disco = set()
    processadas = 0
    puladas = 0

    for caminho in vault_dir.rglob("*.md"):
        rel = str(caminho.relative_to(vault_dir))
        notas_no_disco.add(rel)
        texto = caminho.read_text(encoding="utf-8")
        h = _hash_conteudo(texto)

        # Se a nota já está indexada com o mesmo hash, pula (incremental)
        if hash_por_nota.get(rel) == h:
            puladas += 1
            continue

        # Nota nova ou alterada: remove versão antiga e reindexar
        colecao.delete(where={"nota": rel})
        chunks = _dividir_em_chunks(texto, config.CHUNK_TAMANHO, config.CHUNK_SOBREPOSICAO)
        if chunks:
            colecao.add(
                ids=[f"{rel}::{i}" for i in range(len(chunks))],
                documents=chunks,
                metadatas=[{"nota": rel, "hash": h, "chunk": i} for i in range(len(chunks))],
            )
        processadas += 1

    # Remove do índice notas que não existem mais no disco
    removidas = 0
    for nota in set(hash_por_nota) - notas_no_disco:
        colecao.delete(where={"nota": nota})
        removidas += 1

    return {"processadas": processadas, "puladas": puladas, "removidas": removidas}
