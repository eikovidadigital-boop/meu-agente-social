"""
Agente de textos da arte do post.
Gera os textos curtos que vão NA imagem (título, subtítulo, benefício, tagline),
a partir do nome e info do produto. Responde em JSON para encaixe direto no layout.
Diferente do agente de legendas (que escreve o texto longo da postagem).
"""
import json

from src.llm.client import LLMClient

SYSTEM = (
    "Você cria textos curtos e impactantes para artes de post de uma marca de "
    "óleos naturais (EikoVida). Os textos vão DENTRO da imagem, então são curtos, "
    "em CAIXA ALTA, vendedores e fáceis de ler. Responda APENAS com JSON válido, "
    "sem comentários, sem markdown."
)

TEMPLATE = {
    "titulo": "ÓLEO DE PEQUI",
    "subtitulo": "ENERGIA E VITALIDADE DA NATUREZA",
    "beneficio": ["RICO EM", "VITAMINA A", "E CAROTENOS"],
    "tagline": ["100% NATURAL", "PRENSADO A FRIO"],
}


def _fallback(nome: str) -> dict:
    nome_up = (nome or "ÓLEO NATURAL").upper()
    return {
        "titulo": nome_up[:22],
        "subtitulo": "O PODER DA NATUREZA NA SUA PELE",
        "beneficio": ["100%", "NATURAL", "E PURO"],
        "tagline": ["100% NATURAL", "PRENSADO A FRIO"],
    }


def gerar_textos(produto_nome: str, produto_info: str = "", llm: LLMClient = None) -> dict:
    """Gera os textos da arte para o produto. Sempre devolve dict completo."""
    llm = llm or LLMClient()
    prompt = (
        f"Produto: {produto_nome}\n"
        f"Informações: {produto_info or '(óleo natural prensado a frio)'}\n\n"
        "Gere os textos da arte do post NESTE formato JSON exato:\n"
        f"{json.dumps(TEMPLATE, ensure_ascii=False)}\n\n"
        "Regras: 'titulo' = nome do óleo, máx 22 caracteres. "
        "'subtitulo' = 1 frase de benefício, máx 40 caracteres. "
        "'beneficio' = exatamente 3 linhas MUITO curtas (1-2 palavras cada) destacando "
        "uma vantagem real do produto. 'tagline' = exatamente 2 linhas curtas. "
        "Tudo em CAIXA ALTA, em português. Responda só o JSON."
    )
    try:
        resp = llm.gerar(prompt, system=SYSTEM, max_tokens=400)
        resp = resp.strip().replace("```json", "").replace("```", "").strip()
        dados = json.loads(resp)
        # validação mínima
        for k in ("titulo", "subtitulo", "beneficio", "tagline"):
            if k not in dados:
                raise ValueError(f"falta {k}")
        dados["beneficio"] = [s.upper() for s in dados["beneficio"]][:3]
        dados["tagline"] = [s.upper() for s in dados["tagline"]][:2]
        dados["titulo"] = dados["titulo"].upper()
        dados["subtitulo"] = dados["subtitulo"].upper()
        return dados
    except Exception:
        return _fallback(produto_nome)
