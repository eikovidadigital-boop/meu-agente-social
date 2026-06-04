"""
Relatório Semanal.
Coleta as métricas dos posts publicados na semana, agrega os números
e gera um relatório em markdown salvo no vault (para ler no Obsidian).
"""
from datetime import datetime, timedelta, timezone
from pathlib import Path

from src import config
from src.storage import db


def coletar_metricas(collector, dias: int = 7) -> int:
    """Coleta e salva métricas dos posts publicados nos últimos N dias."""
    desde = (datetime.now(timezone.utc) - timedelta(days=dias)).isoformat()
    pubs = db.publicacoes_publicadas(desde)
    for pub in pubs:
        m = collector.coletar(pub.get("post_id_externo"), pub.get("plataforma"))
        db.salvar_metrica(pub["id"], curtidas=m["curtidas"],
                          comentarios=m["comentarios"], alcance=m["alcance"])
    return len(pubs)


def _montar_markdown(metricas: list[dict], dias: int) -> str:
    hoje = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    total = len(metricas)
    curtidas = sum(m["curtidas"] for m in metricas)
    comentarios = sum(m["comentarios"] for m in metricas)
    alcance = sum(m["alcance"] for m in metricas)

    linhas = [
        f"# 📊 Relatório Semanal — {hoje}",
        "",
        f"Período: últimos {dias} dias",
        "",
        "## Resumo",
        f"- Publicações medidas: **{total}**",
        f"- Curtidas totais: **{curtidas}**",
        f"- Comentários totais: **{comentarios}**",
        f"- Alcance total: **{alcance}**",
    ]

    if total > 0:
        media_alcance = round(alcance / total, 1)
        linhas.append(f"- Alcance médio por post: **{media_alcance}**")
        melhor = max(metricas, key=lambda m: m["alcance"])
        linhas += [
            "",
            "## Destaque",
            f"- Post com maior alcance: publicação #{melhor['publicacao_id']} "
            f"({melhor['alcance']} de alcance, {melhor['curtidas']} curtidas)",
        ]
    else:
        linhas += ["", "_Sem métricas no período._"]

    linhas += ["", "---", "## 🧭 Navegação",
               "[[EikoVida - Projeto]] · [[Agente Social - Resumo de Modulos]]"]
    return "\n".join(linhas)


def gerar_relatorio(dias: int = 7, salvar: bool = True) -> str:
    """Gera o relatório em markdown e (opcionalmente) salva no vault."""
    desde = (datetime.now(timezone.utc) - timedelta(days=dias)).isoformat()
    metricas = db.metricas_periodo(desde)
    md = _montar_markdown(metricas, dias)

    if salvar:
        hoje = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        pasta = Path(config.VAULT_DIR) / "Relatorios"
        pasta.mkdir(parents=True, exist_ok=True)
        (pasta / f"Relatorio Semanal {hoje}.md").write_text(md, encoding="utf-8")
    return md


def executar_semanal(collector, dias: int = 7) -> dict:
    """Fluxo completo: coleta métricas e gera o relatório."""
    coletados = coletar_metricas(collector, dias)
    md = gerar_relatorio(dias, salvar=True)
    return {"posts_medidos": coletados, "relatorio": md}
