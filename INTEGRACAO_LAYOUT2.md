# Layout 2 (informativo) + Compliance ANVISA — como plugar

## O que tem no pacote
- `src/image/arte_informativo.py` — layout 2 (claro/editorial) + `escolher_layout()`. Recusa kit.
- `src/agents/textos_informativo.py` — textos do layout 2 por foco, já compliant + regra ANVISA.
- `src/compliance.py` — guarda-palavras (Meta + Google + ANVISA). Roda antes de publicar.
- `assets/fontes/Montserrat.ttf` — fonte nova do layout 2 (Anton já existe).
- `tests/` — testes (passam local e no Actions).

## Regras embutidas
- Bloqueia cura/trata/previne, "você sofre de", "garantido/comprovado", "milagre".
- Camada ANVISA: bloqueia anti-inflamatório, cicatrizante, antisséptico, analgésico,
  dor/articulação/reumatismo/artrite, repelente, antimicrobiano — em TODOS os produtos.
- COPAÍBA, SUCUPIRA e ANDIROBA: nunca usam foco SAÚDE. Só entram como cosmético
  (pele/cabelo) + recebem instrução extra ANVISA no prompt. (`focos_permitidos()`)

## Subir no GitHub
Add file → Upload files → arrastar `src`, `assets`, `tests` e `INTEGRACAO_LAYOUT2.md` → Commit → rodar "Ciclo Diario".

## Mudanças no `src/pipeline.py`

1) Topo:
```python
from src.image.arte_informativo import montar as montar_informativo, escolher_layout
from src.agents.textos_informativo import gerar_textos as gerar_textos_info
from src.compliance import revisar, suavizar, garantir, focos_permitidos
```

2) Escolher o foco respeitando produtos sensíveis (ANVISA):
```python
permitidos = focos_permitidos(produto.nome)          # remove SAUDE de copaiba/sucupira/andiroba
foco = escolher_foco_dentro(permitidos, indice)      # use sua rotacao, mas só entre os permitidos
```

3) Escolher layout (kit nunca vai pro informativo) e montar:
```python
if escolher_layout(produto.eh_kit, indice) == "informativo":
    t = gerar_textos_info(produto.nome, produto.info, foco, llm)
    arte = montar_informativo(frasco_recortado, nome=t["nome"], foco=foco,
                              tagline3=t["tagline3"], descricao=t["descricao"],
                              beneficios3=t["beneficios3"], volume=produto.volume)
else:
    arte = montar_layout1(...)   # layout dramatico atual. Kit cai aqui por enquanto.
```

4) COMPLIANCE EM TODO TEXTO (vale para os DOIS layouts):
- Legenda, antes de publicar:
```python
if not revisar(legenda).ok:
    legenda = suavizar(legenda)
    if not revisar(legenda).ok:
        legenda = gerar_legenda(...)        # regenerar; se ainda falhar, usar fallback seguro
```
- Textos da arte do LAYOUT 1 (arte_textos.py): passe cada texto por `garantir()`:
```python
beneficio = garantir(beneficio_gerado, fallback="100% puro e natural")
```

## Fora do robô
A página do produto no eikovida.com também é avaliada pelo Meta/Google.
Revisar os textos da loja com a mesma régua — principalmente copaíba, sucupira e andiroba.

---

# Layout 3 — KIT (vários frascos)

- `src/image/arte_kit.py` — `montar_kit(produtos_rgba, nome, itens, tagline3, descricao)`.
  Exige 2+ frascos (produto único vai pro layout 1/2).
- `src/agents/textos_informativo.py` → `gerar_textos_kit(nome_kit, itens, llm)`:
  sempre cosmético/combo, sem claim de saúde. Se algum item for copaíba/sucupira/andiroba,
  mantém 100% cosmético.

No `pipeline.py`, quando `escolher_layout(produto.eh_kit, indice) == "kit"`:
```python
from src.image.arte_kit import montar_kit
from src.agents.textos_informativo import gerar_textos_kit
t = gerar_textos_kit(kit.nome, kit.itens, llm)
arte = montar_kit(frascos_recortados, nome=t["nome"], itens=kit.itens,
                  tagline3=t["tagline3"], descricao=t["descricao"])
```
`frascos_recortados` = lista com o recorte de cada óleo do kit.

## Resumo dos 3 layouts
- Layout 1 (dramático/escuro) — produto único.
- Layout 2 (informativo/claro) — produto único. Alterna com o 1.
- Layout 3 (kit) — só kits.
Compliance roda em todos. Copaíba/sucupira/andiroba nunca usam foco saúde.

---

# Story 9:16 (automático, junto com o feed)

- `src/image/story_arte.py` → `montar_story(produto_rgba, nome, foco, tagline3, cta="eikovida.com")`.
  Formato 1080x1920, frasco protagonista, folhas naturais no fundo, conteúdo na zona segura.
  Reusa o MESMO frasco recortado, foco e tagline do post do dia (compliance já aplicado).

## No `pipeline.py` — depois de montar e publicar o post do feed:
```python
from src.image.story_arte import montar_story

story = montar_story(frasco_recortado, nome=produto.nome, foco=foco, tagline3=t["tagline3"])
url_story = hospedar(story)          # mesma hospedagem que você já usa (raw.githubusercontent)
publicar_story(url_story)            # ver função abaixo
```

## Publicar story pela API (mesma do feed, muda só o tipo)
```python
def publicar_story(image_url):
    # 1) cria container com media_type=STORIES (story NAO usa caption)
    c = requests.post(f"https://graph.facebook.com/v21.0/{IG_USER_ID}/media",
        data={"image_url": image_url, "media_type": "STORIES", "access_token": TOKEN}).json()
    # 2) publica
    requests.post(f"https://graph.facebook.com/v21.0/{IG_USER_ID}/media_publish",
        data={"creation_id": c["id"], "access_token": TOKEN})
```

Observações:
- Precisa da permissão `instagram_content_publish` (já tem, pois publica feed).
- Story conta no limite de 25 publicações/24h (junto com feed). Folgado.
- Link CLICÁVEL (sticker de link) não entra via API — o CTA fica desenhado na imagem.
  Se quiser link clicável, publique o story manual e adicione o sticker.
