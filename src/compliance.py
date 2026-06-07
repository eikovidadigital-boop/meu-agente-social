# -*- coding: utf-8 -*-
"""
Guarda-palavras de compliance (Meta + Google Ads + ANVISA).
Roda ANTES de publicar, em TODO texto (legenda e arte) dos DOIS layouts.

Camadas:
- ALTO/PESSOAL/ARMADILHA: alegacoes de saude/promessa proibidas (todos os produtos).
- TERAPEUTICO: efeito medicinal (anti-inflamatorio, cicatrizante, dor, repelente...).
  Mira o que a ANVISA fiscaliza. Vale para todos, critico para copaiba/sucupira/andiroba.
- SENSIVEIS: produtos sob fiscalizacao reforcada -> nunca usam foco SAUDE (so cosmetico).
"""
import re, unicodedata
from dataclasses import dataclass, field

ALTO = [
    r"\bcur(a|ar|am|ou|ado|ada)\b",
    r"\btrata(r|mento|mentos)?\b(?!\s+de\s+beleza)",
    r"\bprevin(e|ir)\b|\bpreven(ç|c)[ãa]o\b",
    r"\belimina(r|ção)?\s+(a\s+)?(doen|infec|fungo|bactéri|vírus|virus|cândida|candida)",
    r"\bcombat(e|er)\s+(a\s+)?(doen|infec|gripe|virose|inflamaç)",
    r"\brem[ée]dio\b|\bmedicament",
    r"\bdiabet|\bhipertens|\bpress[ãa]o\s+alta|\bcolesterol\b|\bc[âa]ncer\b|\bdepress[ãa]o\b|\bansiedade\b|\bins[ôo]nia\b|\bgastrite\b|\benxaqueca\b",
]
PESSOAL = [
    r"\bvoc[êe]\s+(tem|sofre|est[áa]\s+com|sente|padece)\b",
    r"\bsofre\s+de\b", r"\bcansad[oa]\s+de\b",
    r"\best[áa]\s+com\s+(dor|problema|doen)",
]
ARMADILHA = [
    r"\bgarantid[oa]s?\b|\bgarante\b|\bresultado\s+garantido\b",
    r"\bcomprovad[oa]s?\b|\bclinicamente\b|\bcientificamente\b",
    r"\bmilagr",
    r"\b100%\s+efic|\befic[áa]cia\s+comprovada\b",
    r"\bal[íi]vio\s+(instant[âa]neo|imediato)\b",
    r"\brecomendad[oa]\s+por\s+(m[ée]dicos|dermatolog|especialist)",
    r"\b(reverte|revers[ãa]o\s+d)o?\s+envelhecimento\b",
    r"\belimina(r)?\s+(as\s+)?rugas\b|\bacaba\s+com\s+(a\s+)?(celulite|rugas|manchas)\b",
]
# --- camada ANVISA / efeito terapeutico (vale para TODOS) ---
TERAPEUTICO = [
    r"\banti[\s-]?inflamat[óo]ri[oa]s?\b|\bantiinflamat",
    r"\bcicatrizante\b|\bcicatriza(r|m|ndo)\b",
    r"\bantiss?[ée]ptic|\bass[ée]ptic",
    r"\banalg[ée]sic|\balivi(a|ar)\s+(a\s+)?dor|\bal[íi]vio\s+da\s+dor\b",
    r"\bdor(es)?\s+(muscular|nas?\s+articula|articular|nas?\s+juntas)",
    r"\barticula(ç|c)|\breumat|\bartrit|\bartrose\b|\bgota\b|\b[áa]cido\s+[úu]rico\b",
    r"\binflama(ç|d)",
    r"\bantimicrobian|\bantibacterian|\bantif[úu]ngic|\bantibi[óo]tic|\bantivir",
    r"\brepelente\b|\brepel(e|ir)\s+(inseto|mosquito|pernilongo)",
    r"\bexpectorante\b|\bdescongestionante\b",
    r"\bimunol[óo]gic|\bsistema\s+imun",
]

NIVEIS = [("ALTO", ALTO), ("PESSOAL", PESSOAL), ("ARMADILHA", ARMADILHA), ("TERAPEUTICO", TERAPEUTICO)]

SUAVIZAR = [
    (r"\bque\s+protege\s+as\s+c[ée]lulas\b", "fonte natural de antioxidantes"),
    (r"\baumenta\s+a?\s*imunidade\b", "faz parte de uma alimentação equilibrada"),
    (r"\baumenta\s+a?\s*energia\b", "fonte de nutrientes"),
    (r"\bclinicamente\s+comprovad[oa]\b", ""), (r"\bcomprovad[oa]\b", ""), (r"\bgarantid[oa]\b", ""),
    (r"\bremove\s+(as\s+)?manchas\b", "ajuda a uniformizar a aparência da pele"),
    (r"\belimina(r)?\s+(as\s+)?rugas\b", "ajuda a suavizar a aparência das linhas"),
    (r"\btrata\b", "cuida de"),
]

# produtos sob fiscalizacao reforcada da ANVISA -> nunca foco SAUDE
SENSIVEIS = {"copaiba", "sucupira", "andiroba"}

def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().lower()
    return s

def eh_sensivel(nome: str) -> bool:
    n = _norm(nome)
    return any(s in n for s in SENSIVEIS)

def focos_permitidos(nome: str, focos=("PELE", "CABELO", "SAUDE")):
    """Sensiveis nunca entram como SAUDE (so cosmetico)."""
    if eh_sensivel(nome):
        return [f for f in focos if f != "SAUDE"]
    return list(focos)

@dataclass
class Relatorio:
    ok: bool
    problemas: list = field(default_factory=list)

def revisar(texto: str) -> Relatorio:
    t = texto or ""; probs = []
    for nivel, regras in NIVEIS:
        for r in regras:
            for m in re.finditer(r, t, flags=re.IGNORECASE):
                probs.append((nivel, m.group(0)))
    return Relatorio(ok=(len(probs) == 0), problemas=probs)

def suavizar(texto: str) -> str:
    t = texto
    for pat, rep in SUAVIZAR:
        t = re.sub(pat, rep, t, flags=re.IGNORECASE)
    return re.sub(r"\s{2,}", " ", t).strip(" ,.")

def garantir(texto: str, fallback: str) -> str:
    """Helper para QUALQUER texto (layout 1 ou 2): ok -> usa; senao suaviza; senao fallback."""
    if revisar(texto).ok:
        return texto
    s = suavizar(texto)
    return s if revisar(s).ok else fallback
