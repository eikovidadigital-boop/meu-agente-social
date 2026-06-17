# -*- coding: utf-8 -*-
"""
Trava de compliance das RESPOSTAS de comentário.
Espelha as regras do compliance.py do sistema: nada de claim de saúde.
Os produtos são COSMÉTICOS de uso externo (pele e cabelo).
"""

# Termos que NUNCA podem aparecer numa resposta automática.
# (cobre cura/tratamento + saúde sistêmica)
TERMOS_PROIBIDOS = [
    "cura", "curar", "cure", "tratamento", "tratar", "trata ",
    "remédio", "remedio", "medicina", "medicinal", "medicamento",
    "anti-inflamat", "antiinflamat", "inflamaç", "inflamac", "inflamad",
    "imunidade", "imunológic", "imunologic", "imune",
    "vitalidade", "defesas do corpo", "defesa do corpo",
    "organismo", "de dentro para fora", "de dentro pra fora",
    "emagrec", "perder peso", "queima de gordura",
    "doença", "doenca", "enfermidade", "patologia",
    "colesterol", "diabetes", "pressão alta", "pressao alta",
    "ingerir", "ingestão", "ingestao", "tomar o óleo", "tomar o oleo",
    "via oral", "consumo interno", "uso interno",
    "ansiedade", "depressão", "depressao", "insônia", "insonia",
    "fortalece o sistema", "aumenta a imun", "previne", "prevenir doen",
]


def validar(texto: str):
    """
    Retorna (ok: bool, motivo: str).
    ok=False se a resposta contiver qualquer termo proibido.
    """
    if not texto or not texto.strip():
        return False, "resposta vazia"

    baixo = texto.lower()
    for termo in TERMOS_PROIBIDOS:
        if termo in baixo:
            return False, f"termo proibido: '{termo.strip()}'"

    return True, "ok"
