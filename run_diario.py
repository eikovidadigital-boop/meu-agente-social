"""
Ponto de entrada do ciclo diário (executado pelo GitHub Actions).
Usa as credenciais do ambiente (GitHub Secrets) e as dependências reais.
"""
from src.pipeline import executar_diario

# Imagem-base padrão (produto do site). Pode rotacionar por dia no futuro.
PRODUTO_IMG = "https://eikovida.com/cdn/shop/files/criativos30ml_9.png"


def main():
    resumo = executar_diario(produto_img_url=PRODUTO_IMG)
    print("Resumo do ciclo diário:")
    print(f"  Objetivo : {resumo['objetivo']}")
    print(f"  Ideia    : {resumo['ideia']}")
    print(f"  Imagem   : {resumo['imagem_url']}")
    print(f"  Conteúdos: {resumo['conteudos']}")
    print(f"  Publicações: {resumo['publicacoes']}")


if __name__ == "__main__":
    main()
