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
