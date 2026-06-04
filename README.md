# 🌱 Meu Agente Social (sistema pessoal)

Automação pessoal de redes sociais usando o vault Obsidian como base de conhecimento (RAG).
Roda autônomo via GitHub Actions. Custo ~R$6,60/mês.

## Progresso
- [x] **M1** — RAG (indexação + busca semântica)
- [x] **M2** — Agentes de IA (ideias, legendas, hashtags, prompt)
- [x] **M3** — Geração de imagens (gpt-image-1 + ImgBB)
- [x] **M4** — Storage (SQLite)
- [x] **M5** — Publicação (Instagram + Facebook)
- [x] **M6** — Automação (GitHub Actions diário)
- [x] **M7** — Relatório semanal
- [ ] M8 — TikTok (fase posterior)

## Testes
```bash
pip install -r requirements.txt
python -m pytest tests/ -v
```

## Documentação
Cada módulo documentado em `docs/`. Comece por `docs/M1-rag.md`.
