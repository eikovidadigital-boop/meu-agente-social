# M7 — Relatório Semanal

**Status:** ✅ Concluído e testado (4/4 testes do M7; 32/32 no total)
**Data:** 2026-06-04
**Dependências:** M4 (storage), M5 (publicações)

---

## Objetivo
Medir os resultados: coletar métricas dos posts da semana e gerar um relatório em markdown salvo direto no vault, para acompanhar no Obsidian.

## Arquivos criados
```
src/social/metrics.py        # MetricsCollector (curtidas, comentários, alcance)
src/report/weekly.py         # coleta + agrega + gera relatório no vault
run_semanal.py               # ponto de entrada
.github/workflows/semanal.yml # workflow semanal (domingo)
tests/test_report.py         # 4 testes com coletor falso
```
**Adição justificada ao M4:** `db.publicacoes_publicadas(desde)` — listar posts publicados no período para coletar métricas.

## Como funciona
1. **MetricsCollector** busca, via Graph API, curtidas/comentários (campos da mídia) e alcance (insights) de cada post publicado.
2. **`coletar_metricas`** percorre os posts publicados nos últimos 7 dias e salva as métricas no banco.
3. **`gerar_relatorio`** agrega os números (totais, média de alcance, melhor post) e escreve um markdown em `vault/Relatorios/Relatorio Semanal AAAA-MM-DD.md`.
4. O workflow semanal (domingo ~20h BRT) roda tudo e faz commit do relatório no repo/vault.

## Decisão de arquitetura (registrada)
**Coletor de métricas injetável.** `MetricsCollector` aceita `get_fn` para teste, sem chamar a Graph API. O relatório é salvo como nota no vault, integrando-se ao seu Obsidian (com links de navegação).

## Como usar (exemplo)
```python
from src.report.weekly import executar_semanal
from src.social.metrics import MetricsCollector

resumo = executar_semanal(MetricsCollector(), dias=7)
# -> métricas coletadas + relatório salvo no vault
```

## Testes (resultado)
```
test_coleta_metricas_dos_publicados PASSED
test_gera_relatorio_com_totais PASSED
test_relatorio_vazio_nao_quebra PASSED
test_executar_semanal_completo PASSED
```

## Sistema completo
Com o M7, o núcleo está fechado: gerar (RAG + agentes + imagem) → salvar → publicar → medir → relatar, tudo autônomo na nuvem.

## Próximo (fase futura)
**M8 — TikTok** (API própria + vídeo) e melhorias: rotação de produtos, aprovação manual opcional.

---
## 🧭 Navegação
[[Arquitetura - Sistema Pessoal Automacao Social]] · [[Agente Social - M6 Automacao]] · [[EikoVida - Projeto]] · [[CLAUDE]]
