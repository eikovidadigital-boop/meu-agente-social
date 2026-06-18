# -*- coding: utf-8 -*-
"""
Cerebro do agente de Direct.

Classifica a mensagem do cliente e gera a resposta, com o DETECTOR DE INTENCAO
DE COMPRA: quando o cliente da sinal de querer comprar, ja devolve o LINK direto
do produto.

Regras de atendimento (as mesmas dos comentarios):
  DUVIDA   -> responde SO com a descricao real do produto (products.json).
  POSOLOGIA-> nao orienta uso/dose/ingestao; manda consultar o medico.
  COMPRA   -> simpatico + LINK direto do produto (detector de compra).
  CATALOGO -> passa e-mail suporte@eikovida.com + WhatsApp.
  HUMANO   -> cliente quer falar com atendente/reclamacao -> passa o WhatsApp.
  SAUDACAO -> resposta simpatica curta.
  IGNORAR  -> spam / sem conteudo -> nao responde.

Tudo passa pela trava ANVISA do src/compliance.py (garantir/suavizar).
"""
import json
import os

from src import config
from src import util_net as net
from src import compliance
from src.direct import produtos as prod

EMAIL = "suporte@eikovida.com"
WHATS = "(81) 4141-0577"
WHATS_LINK = "https://wa.me/558141410577"


def _contato():
    return f"📧 {EMAIL}\n📱 WhatsApp: {WHATS} — {WHATS_LINK}"


def _modelo():
    return os.environ.get("ANTHROPIC_MODEL", "claude-3-5-haiku-latest")


def _ia(prompt):
    key = getattr(config, "ANTHROPIC_API_KEY", "") or os.environ.get("ANTHROPIC_API_KEY", "")
    if not key:
        return ""
    r = net.post("https://api.anthropic.com/v1/messages",
                 headers={"x-api-key": key, "anthropic-version": "2023-06-01",
                          "content-type": "application/json"},
                 json={"model": _modelo(), "max_tokens": 500,
                       "messages": [{"role": "user", "content": prompt}]},
                 timeout=45)
    d = r.json()
    if "error" in d:
        raise RuntimeError(d["error"].get("message", "erro IA"))
    return "".join(b.get("text", "") for b in d.get("content", []) if b.get("type") == "text")


PROMPT = """Voce e o atendente da EikoVida (oleos vegetais naturais/veganos) respondendo uma
mensagem no Direct do Instagram. Responda em portugues, simpatico, curto (1-3 frases), humano.

CATALOGO REAL DA LOJA (use SOMENTE o que esta aqui; NUNCA invente uso ou beneficio):
{cardapio}

STATUS DO SITE AGORA: {status_site}

MENSAGEM DO CLIENTE:
"{mensagem}"

Classifique em UM tipo e gere a resposta seguindo as regras:
- DUVIDA: duvida sobre um produto -> responda so com o que esta na descricao real. Se citar um produto, ponha o nome exato dele em "produto".
- POSOLOGIA: pergunta de uso/dose/quanto tomar/como aplicar/ingestao -> NAO oriente; diga gentilmente que trabalham so com oleos vegetais (nao remedios) e que o ideal e consultar o medico.
- COMPRA: cliente quer comprar / pergunta preco / "como compro" / "tem disponivel" / "valor" -> resposta simpatica e ponha em "produto" o nome exato do produto que ele quer.
- CATALOGO: pede catalogo, lista, outras infos gerais -> resposta simpatica (o link/contato eu adiciono depois).
- HUMANO: quer falar com atendente, reclamacao, problema com pedido -> resposta acolhedora dizendo que vai passar pro atendimento.
- SAUDACAO: oi/elogio/agradecimento -> resposta simpatica curta.
- IGNORAR: spam, propaganda, sem sentido -> resposta vazia.

PROIBIDO: prometer cura/tratamento, falar de imunidade/saude sistemica, inventar beneficio.

Responda SO um JSON, sem mais nada:
{{"tipo":"...","resposta":"...","produto":""}}"""


def pensar(mensagem, produtos, cardapio, site_ok=True):
    """Retorna dict pronto pra enviar: {tipo, texto} (texto vazio = nao responder)."""
    bruto = _ia(PROMPT.format(cardapio=cardapio,
                              status_site=("no ar" if site_ok else "fora do ar"),
                              mensagem=mensagem))
    try:
        ini, fim = bruto.find("{"), bruto.rfind("}")
        dados = json.loads(bruto[ini:fim + 1])
    except Exception:
        # Sem IA ou resposta invalida -> cai no contato (seguro)
        return {"tipo": "CATALOGO",
                "texto": compliance.garantir(
                    f"Oi! Pra te ajudar certinho, fala com a gente:\n\n{_contato()}", _contato())}

    tipo = (dados.get("tipo") or "IGNORAR").upper()
    resposta = (dados.get("resposta") or "").strip()
    nome_prod = (dados.get("produto") or "").strip()

    if tipo == "IGNORAR" or not resposta:
        return {"tipo": "IGNORAR", "texto": ""}

    # Detector de intencao de compra: anexa o link direto do produto.
    if tipo == "COMPRA":
        p = prod.achar_produto(nome_prod or mensagem, produtos)
        if p:
            link = prod.link_produto(p)
            preco = prod.preco_produto(p)
            extra = f"\n\n🛍️ {p.get('title','')}"
            if preco:
                extra += f" — {preco}"
            extra += f"\n👉 {link}\n\nEnviamos pra todo o Brasil! 🌿"
            resposta = resposta + extra
        else:
            resposta = resposta + f"\n\nMe diz qual produto que eu te mando o link! Ou veja tudo em {prod.LOJA} 🌿"

    elif tipo == "CATALOGO":
        resposta = resposta + f"\n\n{_contato()}"

    elif tipo == "HUMANO":
        resposta = resposta + f"\n\nVou te encaminhar pro nosso atendimento:\n{_contato()}"

    # Trava ANVISA em toda resposta (suaviza + garante texto seguro)
    seguro = compliance.garantir(compliance.suavizar(resposta), resposta)
    return {"tipo": tipo, "texto": seguro}
