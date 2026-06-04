# M4 — Storage (SQLite)

**Status:** ✅ Concluído e testado (5/5 testes do M4; 20/20 no total)
**Data:** 2026-06-04
**Dependências:** Nenhuma direta (usado por M5, M6, M7)

---

## Objetivo
Persistir tudo num único arquivo SQLite (versionado no repo): o conteúdo gerado, a fila de publicações e as métricas.

## Arquivos criados
```
src/storage/db.py          # camada de persistência (sqlite3 puro)
tests/test_storage.py      # 5 testes com banco temporário
```

## Tabelas
- **conteudo** — id, criado_em, plataforma, ideia, legenda, hashtags, prompt_imagem, imagem_url, status
- **publicacoes** — id, conteudo_id, plataforma, agendado_para, publicado_em, post_id_externo, status, erro
- **metricas** — id, publicacao_id, curtidas, comentarios, alcance, coletado_em

## Funções
- `init_db()` — cria as tabelas
- `salvar_conteudo(...)` / `listar_conteudo()`
- `agendar_publicacao(...)` / `publicacoes_pendentes()`
- `marcar_publicado(id, post_id)` / `marcar_erro(id, erro)`
- `salvar_metrica(...)` / `metricas_periodo(desde_iso)`

## Decisão de arquitetura (registrada)
**SQLite puro (stdlib), sem ORM.** Justificativa: para um sistema pessoal, o `sqlite3` nativo é suficiente, zero dependência extra e mais simples de versionar. Caminho do banco vem do `config.DB_PATH` (sobreposto nos testes por um banco temporário).

## Como usar (exemplo)
```python
from src.storage import db

db.init_db()
cid = db.salvar_conteudo(plataforma="instagram", legenda="...", imagem_url="...")
pid = db.agendar_publicacao(cid, "instagram", agendado_para="2026-06-05T10:00")
for p in db.publicacoes_pendentes():
    ...  # publicar (M5)
db.marcar_publicado(pid, post_id_externo="EXT123")
```

## Testes (resultado)
```
test_salvar_e_listar_conteudo PASSED
test_fluxo_publicacao PASSED
test_marcar_erro PASSED
test_metricas_periodo PASSED
test_metricas_periodo_filtra_antigas PASSED
```

## Preparado para crescer
- Novas colunas/tabelas entram no `SCHEMA` com `CREATE TABLE IF NOT EXISTS`.
- O fluxo de status (rascunho → pendente → publicado/erro) já suporta aprovação manual futura.

## Próximo módulo
**M5 — Publicação (Instagram + Facebook):** ler as publicações pendentes e postar via Graph API, atualizando o status no banco.

---
## 🧭 Navegação
[[Arquitetura - Sistema Pessoal Automacao Social]] · [[Agente Social - M3 Imagens]] · [[EikoVida - Projeto]] · [[CLAUDE]]
