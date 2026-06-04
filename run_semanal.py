"""
Ponto de entrada do relatório semanal (executado pelo GitHub Actions).
Coleta métricas dos posts da semana e gera o relatório no vault.
"""
from src.report.weekly import executar_semanal
from src.social.metrics import MetricsCollector


def main():
    collector = MetricsCollector()
    resumo = executar_semanal(collector, dias=7)
    print(f"Posts medidos: {resumo['posts_medidos']}")
    print("Relatório gerado e salvo no vault (pasta Relatorios).")


if __name__ == "__main__":
    main()
