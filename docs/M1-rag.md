# M1 — RAG (Indexação + Busca Semântica)

**Status:** ✅ Concluído e testado (5/5 testes passando)
**Data:** 2026-06-04
**Dependências:** Nenhuma (módulo base)

---

## Objetivo
O coração do sistema: ler o vault Obsidian, indexar as notas e recuperar **apenas os trechos relevantes** para cada tarefa — nunca o vault inteiro. É o que mantém o custo de tokens baixo.

## Arquivos criados
```
src/
├── config.py              # configuração central (caminhos, parâmetros, credenciais)
└── rag/
    ├── embeddings.py       # função de embedding plugável (local / openai / simple)
    ├── indexer.py          # indexação incremental do vault
    └── search.py           # busca semântica + montagem de contexto
tests/
└── test_rag.py            # 5 testes (indexação, busca, incremental)
```

## Como funciona
1. **Indexação incremental** (`indexer.py`): cada nota `.md` é lida, dividida em chunks de ~500 palavras e armazenada no ChromaDB. Um hash do conteúdo detecta mudanças — só notas novas/alteradas são reprocessadas. Notas removidas do disco saem do índice.
2. **Busca semântica** (`search.py`): recebe uma pergunta e retorna os 3-5 trechos mais relevantes, com o nome da nota de origem e um score.
3. **Embeddings plugáveis** (`embeddings.py`): três motores intercambiáveis.

## Decisão de arquitetura (mudança registrada)
**Embeddings locais em vez da API OpenAI.** Justificativa: gratuito, sem dependência externa para indexar, alinhado às prioridades de simplicidade e baixo custo. O motor é **plugável** via variável `RAG_EMBEDDING`:
- `local` (padrão): modelo ONNX nativo do ChromaDB — gratuito.
- `openai`: API de embeddings (custo ínfimo, sem download) — opção alternativa.
- `simple`: bag-of-words por hashing — usado nos testes (offline, sem download).

Isso desacopla o motor de embedding do resto do código: trocar não exige refatorar indexer nem busca.

## Como usar (exemplo)
```python
from src.rag import indexer, search

indexer.indexar_vault()                       # indexa (incremental)
contexto = search.montar_contexto("óleo para crescimento capilar")
# -> só os trechos relevantes, prontos para o prompt do Claude
```

## Testes (resultado)
```
test_indexacao_inicial PASSED
test_busca_semantica_relevante PASSED
test_incremental_pula_inalteradas PASSED
test_incremental_detecta_mudanca PASSED
test_contexto_nao_vazio PASSED
5 passed
```

## Preparado para crescer
- O motor de embedding troca por uma variável de ambiente.
- O indexer já lida com adição, alteração e remoção de notas.
- A busca devolve contexto pronto para os agentes do M2.

## Próximo módulo
**M2 — Agentes de IA** (ideias, legendas, hashtags, prompt de imagem), consumindo o contexto que o RAG fornece.

---
## 🧭 Navegação
[[Arquitetura - Sistema Pessoal Automacao Social]] · [[EikoVida - Projeto]] · [[PROJETOS INDEX]] · [[CLAUDE]]
