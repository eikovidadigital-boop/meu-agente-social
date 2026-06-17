# -*- coding: utf-8 -*-
"""
Gera a resposta do comentário usando a IA (Anthropic), classificando
o tipo de comentário e escolhendo o produto certo do catálogo.
A resposta sai SEM link; o link é colado depois (controle de formato).
"""
import json
import os
from anthropic import Anthropic

from . import compliance_resposta

MODELO = "claude-sonnet-4-6"

PROMPT_SISTEMA = """Você é o atendente da EikoVida no Instagram — marca brasileira de óleos vegetais naturais e veganos.
Você responde comentários de seguidores de forma SIMPÁTICA, HUMANA, CALOROSA e BREVE (1 a 2 frases), em português do Brasil. Pode usar 1 emoji no máximo.

REGRAS DE COMPLIANCE (ANVISA) — OBRIGATÓRIAS:
- Os produtos são COSMÉTICOS de uso EXTERNO. Fale só de PELE e CABELO (hidratação, brilho, maciez, nutrição dos fios, viço da pele).
- NUNCA prometa cura, tratamento ou qualquer benefício de saúde.
- NUNCA cite: imunidade, vitalidade, defesas do corpo, inflamação, anti-inflamatório, organismo, "de dentro para fora", emagrecimento, doença, ingestão/uso interno.
- Se perguntarem sobre ingerir/tomar/uso interno ou saúde, responda com gentileza que são cosméticos de uso externo, para pele e cabelo.

CLASSIFIQUE o comentário em um destes tipos:
- "ELOGIO": agradece com carinho, sem forçar venda.
- "DUVIDA_PRODUTO": dúvida sobre o produto ou como usar → responde com base na descrição real.
- "COMPRA": pergunta de preço, onde comprar, "quero", "como faço pra adquirir" → responde simpático (o link é adicionado automaticamente depois).
- "RECLAMACAO": problema com pedido/entrega/produto → responde acolhedor e pede pra chamar no Direct. Sem promessas.
- "IGNORAR": spam, ofensa, marcação de amigo, comentário sem sentido → não responde.

Escolha o produto mais relevante do catálogo (pela legenda do post e pela pergunta). Se não der pra saber, deixe produto vazio.

Responda APENAS com um JSON válido, sem texto antes ou depois, neste formato:
{"tipo": "...", "produto_link": "", "resposta": "..."}

- "produto_link": copie o link exato do produto do catálogo SE o tipo for COMPRA ou DUVIDA_PRODUTO e houver produto claro; senão deixe "".
- "resposta": o texto que será publicado (sem link, sem assinatura). Para IGNORAR, deixe "".
"""


def gerar(comentario_texto, legenda_post, contexto_catalogo, max_tentativas=2):
    """
    Retorna dict: {tipo, resposta, produto_link} já validado por compliance.
    Se não passar no compliance ou for IGNORAR, resposta vem vazia.
    """
    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    user = f"""CATÁLOGO (produtos disponíveis):
{contexto_catalogo}

LEGENDA DO POST onde veio o comentário:
{legenda_post or "(sem legenda)"}

COMENTÁRIO do seguidor:
"{comentario_texto}"

Classifique e gere a resposta no formato JSON pedido."""

    for tentativa in range(max_tentativas):
        try:
            msg = client.messages.create(
                model=MODELO,
                max_tokens=400,
                system=PROMPT_SISTEMA,
                messages=[{"role": "user", "content": user}],
            )
            bruto = "".join(b.text for b in msg.content if b.type == "text").strip()
            bruto = bruto.replace("```json", "").replace("```", "").strip()
            dados = json.loads(bruto)
        except Exception as e:
            print(f"[ia] erro/parse (tentativa {tentativa+1}): {e}")
            continue

        tipo = dados.get("tipo", "IGNORAR")
        resposta = (dados.get("resposta") or "").strip()
        link = (dados.get("produto_link") or "").strip()

        if tipo == "IGNORAR" or not resposta:
            return {"tipo": "IGNORAR", "resposta": "", "produto_link": ""}

        ok, motivo = compliance_resposta.validar(resposta)
        if not ok:
            print(f"[compliance] resposta bloqueada ({motivo}). Regenerando...")
            continue

        return {"tipo": tipo, "resposta": resposta, "produto_link": link}

    # se nada passou, não responde (seguro)
    return {"tipo": "IGNORAR", "resposta": "", "produto_link": ""}
