"""
Agente de textos da arte do post.
Gera os textos curtos que vão NA imagem (título, subtítulo, benefício, tagline),
a partir do nome e info do produto, SEMPRE focando em UM único ângulo
(pele, cabelo OU saúde) — nunca misturando beleza com saúde no mesmo post.
Os focos se alternam a cada vez que o produto reaparece, criando variações.
Responde em JSON para encaixe direto no layout.
"""
import json

from src.llm.client import LLMClient

# Focos possíveis de um post. Cada um é UM ângulo coerente; beleza (pele/cabelo)
# e saúde nunca aparecem juntas no mesmo post.
FOCOS = [
    {
        "id": "PELE",
        "rotulo": "cuidados com a PELE",
        "desc": "BELEZA DA PELE: hidratação, viço, firmeza, manchas, anti-idade. "
                "Fale SOMENTE de pele. NÃO cite saúde, imunidade nem uso interno.",
    },
    {
        "id": "CABELO",
        "rotulo": "cuidados com o CABELO",
        "desc": "BELEZA DOS CABELOS: força, brilho, crescimento, pontas, couro cabeludo. "
                "Fale SOMENTE de cabelo. NÃO cite saúde, imunidade nem uso interno.",
    },
    {
        "id": "SAUDE",
        "rotulo": "saúde e bem-estar",
        "desc": "SAÚDE E BEM-ESTAR: antioxidante, imunidade, energia, vitalidade, "
                "uso interno/culinário quando fizer sentido. NÃO cite pele nem cabelo.",
    },
]


def escolher_foco(indice: int, n_produtos: int) -> dict:
    """
    Escolhe o foco do post de forma que ele se ALTERNE a cada vez que o mesmo
    produto reaparece. Como o produto é escolhido por rotação (indice % n_produtos),
    a cada \'volta\' completa pela lista de produtos o foco avança. Assim o mesmo
    óleo é apresentado por ângulos diferentes ao longo do tempo.
    """
    n_produtos = max(1, n_produtos)
    volta = indice // n_produtos
    return FOCOS[volta % len(FOCOS)]


SYSTEM = (
    "Você cria textos curtos e impactantes para artes de post de uma marca de "
    "óleos vegetais naturais (EikoVida). Os textos vão DENTRO da imagem: curtos, "
    "em CAIXA ALTA, vendedores e fáceis de ler. Cada post tem UM único foco e você "
    "NUNCA mistura beleza (pele/cabelo) com saúde no mesmo post. "
    "Responda APENAS com JSON válido, sem comentários, sem markdown."
)

TEMPLATE = {
    "titulo": "ÓLEO DE PEQUI",
    "subtitulo": "FRESCOR E VIÇO PARA SUA PELE",
    "beneficio": ["HIDRATAÇÃO", "PROFUNDA", "E DURADOURA"],
    "tagline": ["100% NATURAL", "PRENSADO A FRIO"],
}

_FALLBACK_FOCO = {
    "PELE": ("NUTRIÇÃO PROFUNDA PARA A PELE", ["HIDRATA", "E PROTEGE", "A PELE"]),
    "CABELO": ("FORÇA E BRILHO PARA OS FIOS", ["FORTALECE", "OS FIOS", "COM BRILHO"]),
    "SAUDE": ("SAÚDE E BEM-ESTAR NATURAIS", ["RICO EM", "ANTIOXIDANTES", "NATURAIS"]),
}


def _fallback(nome: str, foco: dict) -> dict:
    sub, ben = _FALLBACK_FOCO.get(foco["id"], _FALLBACK_FOCO["PELE"])
    return {
        "titulo": (nome or "ÓLEO NATURAL").upper()[:22],
        "subtitulo": sub,
        "beneficio": ben,
        "tagline": ["100% NATURAL", "PRENSADO A FRIO"],
        "foco": foco["id"],
    }


def gerar_textos(produto_nome: str, produto_info: str = "", foco: dict = None,
                 llm: LLMClient = None) -> dict:
    """
    Gera os textos da arte para o produto, focados EXCLUSIVAMENTE em um ângulo
    (pele, cabelo ou saúde). Sempre devolve dict completo (com a chave \'foco\').
    """
    foco = foco or FOCOS[0]
    llm = llm or LLMClient()
    prompt = (
        f"Produto: {produto_nome}\n"
        f"Informações: {produto_info or '(óleo vegetal natural prensado a frio)'}\n\n"
        f"FOCO OBRIGATÓRIO DESTE POST: {foco['desc']}\n\n"
        "Gere os textos da arte focando SOMENTE neste ângulo, usando um benefício "
        "REAL do óleo para esse foco. REGRA CRÍTICA: não misture saúde com beleza - "
        "se o foco é pele ou cabelo, fale só de beleza; se é saúde, fale só de "
        "saúde/bem-estar.\n\n"
        "Formato JSON exato:\n"
        f"{json.dumps(TEMPLATE, ensure_ascii=False)}\n\n"
        "Regras: 'titulo' = nome do óleo, máx 22 caracteres. "
        "'subtitulo' = 1 frase de benefício do FOCO, máx 40 caracteres. "
        "'beneficio' = exatamente 3 linhas MUITO curtas (1-2 palavras) sobre o FOCO. "
        "'tagline' = exatamente 2 linhas curtas. Tudo em CAIXA ALTA, em português. "
        "Responda só o JSON."
    )
    try:
        resp = llm.gerar(prompt, system=SYSTEM, max_tokens=400)
        resp = resp.strip().replace("```json", "").replace("```", "").strip()
        dados = json.loads(resp)
        for k in ("titulo", "subtitulo", "beneficio", "tagline"):
            if k not in dados:
                raise ValueError(f"falta {k}")
        dados["beneficio"] = [s.upper() for s in dados["beneficio"]][:3]
        dados["tagline"] = [s.upper() for s in dados["tagline"]][:2]
        dados["titulo"] = dados["titulo"].upper()
        dados["subtitulo"] = dados["subtitulo"].upper()
        dados["foco"] = foco["id"]
        return dados
    except Exception:
        return _fallback(produto_nome, foco)
