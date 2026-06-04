# M3 — Geração de Imagens

**Status:** ✅ Concluído e testado (4/4 testes do M3; 15/15 no total)
**Data:** 2026-06-04
**Dependências:** M2 (prompt de imagem)

---

## Objetivo
Transformar o prompt gerado pelo agente de imagem numa imagem publicável: criar com gpt-image-1 (usando a foto real do produto como base quando disponível) e hospedar no ImgBB, devolvendo uma URL pública.

## Arquivos criados
```
src/image/generator.py     # classe ImageGenerator (gerar, hospedar, criar)
tests/test_image.py        # 4 testes com chamadas falsas injetadas
```

## Como funciona
- **`gerar(prompt, produto_img_url)`**
  - Com `produto_img_url`: baixa a foto do produto e usa o endpoint *edits* (img2img) — mantém o produto real como base, aplicando o estilo da marca.
  - Sem produto: usa *generations* (gera do zero).
  - Retorna a imagem em base64.
- **`hospedar(b64)`**: envia ao ImgBB e devolve a URL pública (permanente).
- **`criar(prompt, produto_img_url)`**: orquestra os dois — é o método que o resto do sistema chama.

## Decisão de arquitetura (registrada)
**Injeção de dependência nas chamadas externas.** `ImageGenerator` aceita `gerar_fn` e `hospedar_fn` opcionais. Em produção, faz as chamadas reais (OpenAI/ImgBB); em teste, recebe funções falsas. Justificativa: testar a orquestração sem custo de API e sem depender de rede.

## Como usar (exemplo)
```python
from src.image.generator import ImageGenerator
from src.agents import image_prompt

prompt = image_prompt.gerar_prompt_imagem("óleo de alecrim")
gen = ImageGenerator()
url = gen.criar(prompt, produto_img_url="https://eikovida.com/cdn/shop/files/criativos30ml_9.png")
# -> URL pública pronta para o módulo de publicação
```

## Testes (resultado)
```
test_criar_orquestra_gerar_e_hospedar PASSED
test_img2img_recebe_url_do_produto PASSED
test_text2img_sem_produto PASSED
test_erro_na_geracao_propaga PASSED
```

## Preparado para crescer
- Trocar o provedor de imagem = trocar a implementação de `gerar`.
- Trocar o host de imagem (ImgBB → outro) = trocar `hospedar`.
- O fallback (sem produto → gera do zero) já está embutido.

## Próximo módulo
**M4 — Storage (SQLite):** salvar o conteúdo gerado, a agenda de publicação e as métricas.

---
## 🧭 Navegação
[[Arquitetura - Sistema Pessoal Automacao Social]] · [[Agente Social - M2 Agentes]] · [[EikoVida - Projeto]] · [[CLAUDE]]
