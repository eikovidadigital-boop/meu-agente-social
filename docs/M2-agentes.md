# M2 — Agentes de IA

**Status:** ✅ Concluído e testado (6/6 testes do M2; 11/11 no total)
**Data:** 2026-06-04
**Dependências:** M1 (RAG)

---

## Objetivo
Os agentes que geram o conteúdo, consumindo o contexto relevante que o RAG fornece — sem nunca carregar o vault inteiro.

## Arquivos criados
```
src/
├── llm/
│   └── client.py           # wrapper da API Claude (injeção p/ testes)
└── agents/
    ├── ideas.py            # gera ideias de conteúdo (RAG)
    ├── captions.py         # legendas por plataforma (IG/FB/TikTok)
    ├── hashtags.py         # hashtags com rotação anti-repetição
    └── image_prompt.py     # prompt de imagem com identidade visual
tests/
└── test_agents.py          # 6 testes com LLM falso injetado
```

## Como funciona
- **LLMClient:** ponto único de chamada ao Claude. Aceita uma função de geração injetada — nos testes, um LLM falso devolve respostas fixas (sem custo de API, determinístico). Usa Haiku por padrão (barato) e expõe Sonnet para tarefas estratégicas.
- **ideas:** recupera contexto (estratégia/produtos/mercado) e gera N ideias, uma por linha.
- **captions:** adapta a legenda ao estilo de cada plataforma (Instagram, Facebook, TikTok); a voz da marca vem do RAG.
- **hashtags:** gera um pool via LLM, mantém um conjunto base fixo (marca) e sorteia o restante — nunca repete o mesmo conjunto.
- **image_prompt:** gera prompt em inglês para o gerador de imagem, com a identidade visual da marca.

## Decisão de arquitetura (registrada)
**Injeção de dependência no LLM.** Cada agente recebe um `llm` opcional. Em produção usa a API real; em teste recebe um falso. Justificativa: testes rápidos, determinísticos e sem gastar API — e desacopla os agentes do provedor de LLM.

## Como usar (exemplo)
```python
from src.agents import ideas, captions, hashtags, image_prompt

lista = ideas.gerar_ideias("crescimento orgânico no Instagram", n=3)
legenda_ig = captions.gerar_legenda(lista[0], "instagram")
tags = hashtags.gerar_hashtags(lista[0], n=15, base=["#eikovida"])
prompt_img = image_prompt.gerar_prompt_imagem(lista[0])
```

## Testes (resultado)
```
test_ideias_parse_linhas PASSED
test_ideias_usa_contexto_rag PASSED
test_legenda_instagram_vs_facebook PASSED
test_legenda_plataforma_invalida PASSED
test_hashtags_inclui_base_e_rotaciona PASSED
test_image_prompt_usa_contexto PASSED
```

## Preparado para crescer
- Trocar de Haiku para Sonnet por agente é só um parâmetro.
- Adicionar uma plataforma nova = uma entrada no dicionário de estilos.
- O LLM falso facilita testar qualquer agente futuro.

## Próximo módulo
**M3 — Geração de Imagens** (gpt-image-1 a partir da foto do produto + hospedagem ImgBB), consumindo o prompt que o agente de imagem gera.

---
## 🧭 Navegação
[[Arquitetura - Sistema Pessoal Automacao Social]] · [[Agente Social - M1 RAG]] · [[EikoVida - Projeto]] · [[CLAUDE]]
