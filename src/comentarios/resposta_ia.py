# -*- coding: utf-8 -*-
"""
Gera a resposta do comentário usando a IA (Anthropic).
Regras de negócio da EikoVida:
- Dúvida de produto: responde APENAS com o que está escrito na descrição da loja.
  Se a info não estiver lá, NÃO inventa -> encaminha contato.
- Posologia / como aplicar / pode tomar: NÃO orienta -> manda consultar o médico
  (trabalhamos só com óleos vegetais, não remédios).
- Catálogo / outras infos: encaminha e-mail e WhatsApp.
A resposta sai SEM link/contato; o "anexo" é colado depois pelo run (controle de formato).
"""
import json
import os
from anthropic import Anthropic

from . import compliance_resposta

MODELO = "claude-sonnet-4-6"

# ---- Contatos oficiais de atendimento ----
CONTATO_EMAIL = "suporte@eikovida.com"
CONTATO_WHATSAPP = "(81) 4141-0577"
CONTATO_WHATSAPP_LINK = "https://wa.me/558141410577"


def bloco_contato() -> str:
    return f"📧 {CONTATO_EMAIL}\n📱 WhatsApp: {CONTATO_WHATSAPP}"


PROMPT_SISTEMA = """Você é o atendente da EikoVida no Instagram — marca brasileira de óleos vegetais naturais e veganos.
Você responde comentários de seguidores de forma SIMPÁTICA, HUMANA, CALOROSA e BREVE (1 a 2 frases), em português do Brasil. Pode usar 1 emoji no máximo.

REGRAS OBRIGATÓRIAS:

1) SÓ O QUE ESTÁ ESCRITO NA LOJA
- Sobre produtos, responda APENAS com a informação que está na descrição do produto fornecida abaixo.
- NUNCA invente, suponha ou complete com conhecimento próprio.
- Se a informação pedida NÃO estiver na descrição, NÃO invente: use o tipo "CONTATO" e oriente a pessoa a falar com o atendimento.

2) NADA DE POSOLOGIA / USO (livra a marca de responsabilidade)
- Se perguntarem dosagem, quantidade, frequência, "como uso", "como passo na pele", "quantas gotas", "pode tomar/ingerir", "como aplico" → use o tipo "POSOLOGIA".
- Nesse caso, responda com gentileza que vocês trabalham apenas com óleos vegetais (não são remédios) e que, para orientação de uso, o ideal é a pessoa conversar com o médico dela. NUNCA oriente uso/dose.

3) COMPLIANCE (ANVISA)
- Os produtos são COSMÉTICOS de uso externo. Fale só de PELE e CABELO.
- NUNCA prometa cura, tratamento ou benefício de saúde. NUNCA cite imunidade, vitalidade, inflamação, anti-inflamatório, organismo, "de dentro para fora", emagrecimento, doença.

CLASSIFIQUE o comentário em um destes tipos:
- "ELOGIO": agradece com carinho, sem forçar venda. (anexar: NADA)
- "DUVIDA_PRODUTO": dúvida respondível com a descrição da loja. (anexar: LINK)
- "COMPRA": pergunta de preço, onde comprar, "quero". (anexar: LINK)
- "POSOLOGIA": pergunta de dose/uso/aplicação/ingestão → mandar consultar o médico. (anexar: NADA)
- "SITE": comentário dizendo que o site está fora do ar, não abre, não carrega, caiu, link não funciona, ou está em manutenção.
    * Veja o "STATUS DO SITE AGORA" informado abaixo.
    * Se o status for "no ar": responda de forma simpática que vocês já estão de volta e a pessoa pode acessar normalmente. (anexar: LINK, e produto_link = "https://eikovida.com")
    * Se o status for "fora do ar": responda que estão em manutenção e voltam em breve, pedindo um pouquinho de paciência. (anexar: NADA)
- "CONTATO": pergunta sobre catálogo, outras infos, ou algo que NÃO está na descrição da loja. (anexar: CONTATO)
- "RECLAMACAO": problema com pedido/entrega → acolhe e pede pra falar com o atendimento. (anexar: CONTATO)
- "SITE_STATUS": a pessoa pergunta ou reclama que o SITE está fora do ar, não abre, não carrega, "caiu", "link quebrado", "não consigo acessar". (anexar: NADA — o sistema cuida da resposta automaticamente)
- "IGNORAR": spam, ofensa, marcação de amigo, sem sentido → não responde. (anexar: NADA)

Escolha o produto mais relevante do catálogo (pela legenda do post e pela pergunta). Se não houver produto claro, deixe produto_link vazio.

Responda APENAS com um JSON válido, sem texto antes ou depois:
{"tipo": "...", "produto_link": "", "anexar": "LINK|CONTATO|NADA", "resposta": "..."}

- "produto_link": copie o link EXATO do produto do catálogo só quando fizer sentido (COMPRA/DUVIDA_PRODUTO); senão "".
- "resposta": o texto publicado (sem link, sem e-mail, sem telefone, sem assinatura). Para IGNORAR, deixe "".
"""


def gerar(comentario_texto, legenda_post, contexto_catalogo, max_tentativas=2):
    """
    Retorna dict: {tipo, resposta, produto_link, anexar} já validado por compliance.
    Se não passar no compliance ou for IGNORAR, resposta vem vazia.
    """
    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    user = f"""CATÁLOGO (produtos e descrições da loja — use SÓ o que está aqui):
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
        anexar = (dados.get("anexar") or "NADA").strip().upper()
        if anexar not in ("LINK", "CONTATO", "NADA"):
            anexar = "NADA"

        # o sistema monta a resposta do site na hora (checagem real); IA só classifica
        if tipo == "SITE_STATUS":
            return {"tipo": "SITE_STATUS", "resposta": "", "produto_link": "", "anexar": "NADA"}

        if tipo == "IGNORAR" or not resposta:
            return {"tipo": "IGNORAR", "resposta": "", "produto_link": "", "anexar": "NADA"}

        ok, motivo = compliance_resposta.validar(resposta)
        if not ok:
            print(f"[compliance] resposta bloqueada ({motivo}). Regenerando...")
            continue

        return {"tipo": tipo, "resposta": resposta, "produto_link": link, "anexar": anexar}

    # se nada passou, encaminha pro atendimento humano (seguro)
    return {"tipo": "CONTATO", "resposta": "Oi! Pra te ajudar certinho, fala com a gente 💚",
            "produto_link": "", "anexar": "CONTATO"}
