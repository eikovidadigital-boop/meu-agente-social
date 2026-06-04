# M5 — Publicação (Instagram + Facebook)

**Status:** ✅ Concluído e testado (5/5 testes do M5; 25/25 no total)
**Data:** 2026-06-04
**Dependências:** M3 (imagem), M4 (storage)

---

## Objetivo
Ler as publicações pendentes do banco e postar de verdade no Instagram e Facebook via Graph API oficial, atualizando o status. Reaproveita a lógica validada no agente EPICO, agora modular.

## Arquivos criados
```
src/social/
├── instagram.py          # InstagramPublisher (container + publish + comentário)
├── facebook.py           # FacebookPublisher (foto na Página)
└── publisher.py          # orquestrador: lê pendentes, publica, atualiza status
tests/test_social.py      # 5 testes com HTTP falso injetado
```
**Adição justificada ao M4:** `db.obter_conteudo(id)` — o publicador precisa buscar um conteúdo específico por id.

## Como funciona
- **InstagramPublisher:** cria o container de mídia → aguarda processamento → publica → coloca hashtags no 1º comentário.
- **FacebookPublisher:** posta a foto na Página com legenda + hashtags no texto.
- **Publisher (orquestrador):** percorre as publicações pendentes, escolhe o adapter pela plataforma, publica e marca `publicado` (com o id externo) ou `erro` (com a mensagem). Erros não derrubam o lote — cada publicação é tratada isoladamente.

## Anti-banimento
- API oficial da Meta (método sancionado).
- Intervalo aleatório de 30-90s entre publicações (evita padrão robótico).
- Hashtags no comentário no Instagram (legenda limpa).
- (O jitter do horário de início fica no M6, na automação.)

## Decisão de arquitetura (registrada)
**Injeção de dependência no HTTP e no sleep.** Os adapters aceitam `post_fn` e `sleep_fn`; o orquestrador aceita `sleep_fn`. Justificativa: testar todo o fluxo de publicação sem chamar a Graph API e sem esperas reais. Também corrigido `datetime.utcnow()` (depreciado) para `datetime.now(timezone.utc)`.

## Como usar (exemplo)
```python
from src.social.instagram import InstagramPublisher
from src.social.facebook import FacebookPublisher
from src.social.publisher import Publisher

pub = Publisher([InstagramPublisher(), FacebookPublisher()])
resultados = pub.publicar_pendentes()   # publica tudo que está pendente no banco
```

## Testes (resultado)
```
test_instagram_fluxo_completo PASSED
test_instagram_erro_no_container PASSED
test_facebook_posta_com_hashtags PASSED
test_publisher_marca_publicado PASSED
test_publisher_marca_erro PASSED
```

## Preparado para crescer
- Nova rede = novo adapter com atributo `.plataforma` e método `publicar`.
- O orquestrador trabalha com qualquer lista de adapters.

## Próximo módulo
**M6 — Automação (GitHub Actions):** o pipeline diário que junta tudo — indexa, gera, salva, publica — rodando sozinho na nuvem.

---
## 🧭 Navegação
[[Arquitetura - Sistema Pessoal Automacao Social]] · [[Agente Social - M4 Storage]] · [[EikoVida - Projeto]] · [[CLAUDE]]
