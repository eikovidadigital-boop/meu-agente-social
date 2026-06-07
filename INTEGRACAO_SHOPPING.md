# Instagram Shopping — etiqueta de produto (link de compra)

Catálogo já aprovado. Falta só ligar a etiqueta no código (já feito) + 1 secret.

## 1. Cadastrar o secret CATALOG_ID
GitHub → repo meu-agente-social → Settings → Secrets and variables → Actions →
New repository secret:
- Name: `CATALOG_ID`
- Secret: `236595792091491`

## 2. Reel — já está pronto
O `run_reel.py` já casa o produto do dia com o catálogo e anexa a etiqueta.
O `publicar-reel.yml` já passa o `CATALOG_ID`. Nada a fazer.

## 3. Feed — 3 passos
a) Substituir `src/social/instagram.py` pela versao deste pacote (aceita product_tags).
b) No `pipeline.py`, antes de publicar o feed:
```python
from src.social_shopping import tags_para, ids_shopify
tags = tags_para(produto.nome, retailer_ids=ids_shopify(produto))  # casa o item EXATO (30ml/120ml/kit)
publisher.publicar(image_url, legenda, hashtags, product_tags=tags)
```
c) No workflow `Ciclo Diario`, adicionar no bloco env:
```yaml
      CATALOG_ID: ${{ secrets.CATALOG_ID }}
```

## Observacoes
- Casa o item EXATO: 1º pelo código da Shopify (retailer_id), 2º pelo nome COM volume.
  Distingue 30ml, 120ml e kit do mesmo óleo. Produto fora do catálogo: publica SEM etiqueta.
- Produto novo: entra sozinho. O products.json e o catálogo Meta são lidos ao vivo a cada
  execução — basta a Shopify estar sincronizando os produtos com o catálogo (a integração faz isso).
- Story NAO aceita etiqueta de produto via API — segue com "link na bio".
- Se aparecer erro de etiqueta no log (permissao), o post/reel sai sem ela. Nesse caso
  o token precisa ser gerado com escopo de Shopping (catalog_management /
  instagram_shopping_tag_products). Me avise que te passo o passo.
