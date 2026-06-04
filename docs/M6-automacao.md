# M6 — Automação (GitHub Actions)

**Status:** ✅ Concluído e testado (3/3 testes do M6; 28/28 no total)
**Data:** 2026-06-04
**Dependências:** M1 a M5 (amarra todos)

---

## Objetivo
Juntar todos os módulos num pipeline diário e fazê-lo rodar sozinho na nuvem, sem PC, via GitHub Actions.

## Arquivos criados
```
src/pipeline.py                  # orquestra o fluxo diário completo
run_diario.py                    # ponto de entrada (executado pelo Actions)
.github/workflows/diario.yml     # agenda + execução + salva estado no repo
tests/test_pipeline.py           # 3 testes com dependências falsas
```

## Fluxo do pipeline (`executar_diario`)
1. Indexa o vault (incremental).
2. Gera a **ideia do dia** (educativo Seg/Qua/Sex; conversão Ter/Qui).
3. Gera o **prompt** e a **imagem** — uma só, reaproveitada nas plataformas (feed coeso).
4. Para cada plataforma: gera **legenda** + **hashtags**, salva no banco e agenda.
5. **Publica** os pendentes (Instagram + Facebook).
6. Retorna um resumo do ciclo.

## Automação (GitHub Actions)
- **Agenda:** Seg/Qua/Sex ~10h BRT e Ter/Qui ~19h BRT (cron).
- **Anti-ban:** espera aleatória de 0-25 min antes de publicar.
- **Estado:** após rodar, faz commit do `data/` (banco SQLite + índice) de volta no repo — assim o estado persiste entre execuções, mesmo sendo a nuvem stateless.
- **Manual:** botão "Run workflow" para testar na hora.

## Decisão de arquitetura (registrada)
**Pipeline com dependências injetáveis.** `executar_diario` aceita `llm`, `image_gen` e `publisher` opcionais. Em produção usa os reais; em teste, falsos. Justificativa: testar o fluxo ponta a ponta sem nenhuma chamada externa. Decisão: **uma imagem por dia, reaproveitada** nas plataformas — coesão visual e economia.

## Como rodar (produção)
1. Subir o projeto num repositório **privado** no GitHub.
2. Adicionar os 6 Secrets (Anthropic, OpenAI, ImgBB, IG_ACCOUNT_ID, FACEBOOK_PAGE_ID, PAGE_ACCESS_TOKEN).
3. Aba Actions → habilitar → roda sozinho na agenda.
4. Testar agora: Actions → Ciclo Diario → Run workflow.

## Testes (resultado)
```
test_pipeline_gera_e_publica PASSED
test_objetivo_do_dia_retorna_texto PASSED
test_pipeline_uma_plataforma PASSED
```

## Preparado para crescer
- Adicionar plataforma = incluir na lista `plataformas`.
- Trocar agenda = editar o cron.
- O `run_diario.py` é o único ponto que muda para ajustes de produção.

## Próximo módulo
**M7 — Relatório Semanal:** coletar métricas dos posts e gerar um relatório que vai pro vault.

---
## 🧭 Navegação
[[Arquitetura - Sistema Pessoal Automacao Social]] · [[Agente Social - M5 Publicacao]] · [[EikoVida - Projeto]] · [[CLAUDE]]
