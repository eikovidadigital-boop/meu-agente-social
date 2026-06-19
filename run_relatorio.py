# -*- coding: utf-8 -*-
"""
Gera o relatorio mensal e salva em data/relatorios/AAAA-MM.md (o workflow commita).
Roda sozinho via .github/workflows/relatorio.yml (dia 1 de cada mes).
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from src import tempo
from src.relatorio import insights


def main():
    dados = insights.coletar()
    md = insights.montar_markdown(dados)
    pasta = os.path.join("data", "relatorios")
    os.makedirs(pasta, exist_ok=True)
    caminho = os.path.join(pasta, f"{tempo.mes_ref()}.md")
    with open(caminho, "w", encoding="utf-8") as f:
        f.write(md)
    print(f"Relatorio salvo: {caminho}")
    print("-" * 50)
    print(md)


if __name__ == "__main__":
    main()
