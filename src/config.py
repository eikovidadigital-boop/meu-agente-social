"""
Configuração central do sistema pessoal de automação social.
Lê variáveis de ambiente (definidas como GitHub Secrets em produção)
com valores padrão para desenvolvimento local.
"""
import os
from pathlib import Path

# Caminhos base do projeto
RAIZ = Path(__file__).resolve().parent.parent
VAULT_DIR = Path(os.environ.get("VAULT_DIR", RAIZ / "vault"))
DATA_DIR = Path(os.environ.get("DATA_DIR", RAIZ / "data"))
CHROMA_DIR = DATA_DIR / "chroma"
DB_PATH = DATA_DIR / "agente.db"

# Assets da arte (fontes e logo) — versionados no repo
ASSETS_DIR = Path(os.environ.get("ASSETS_DIR", RAIZ / "assets"))
FONTE_TITULO = ASSETS_DIR / "fontes" / "Anton.ttf"
FONTE_TEXTO = ASSETS_DIR / "fontes" / "Montserrat-ExtraBold.ttf"
LOGO_PATH = ASSETS_DIR / "logo.png"


# RAG
CHUNK_TAMANHO = 500          # tamanho alvo de cada chunk (em palavras aproximadas)
CHUNK_SOBREPOSICAO = 50      # sobreposição entre chunks (mantém contexto)
BUSCA_TOP_K = 5              # quantos trechos a busca retorna

# Catálogo de produtos reais (imagens verdadeiras do Shopify)
CATALOGO_PATH = Path(os.environ.get("CATALOGO_PATH", RAIZ / "dados" / "catalogo.txt"))
# Loja Shopify: se preenchida, o sistema puxa os produtos automaticamente
SHOPIFY_LOJA = os.environ.get("SHOPIFY_LOJA", "https://eikovida.com")

# Credenciais externas (preenchidas via ambiente/GitHub Secrets)
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
IMGBB_API_KEY = os.environ.get("IMGBB_API_KEY", "")
IG_ACCOUNT_ID = os.environ.get("IG_ACCOUNT_ID", "")
FACEBOOK_PAGE_ID = os.environ.get("FACEBOOK_PAGE_ID", "")
PAGE_ACCESS_TOKEN = os.environ.get("PAGE_ACCESS_TOKEN", "")

# Hospedagem de imagem via GitHub (repo público + raw URL; o Instagram aceita)
GH_TOKEN = os.environ.get("GH_TOKEN", "")
GH_IMAGES_REPO = os.environ.get("GH_IMAGES_REPO", "")  # ex.: "usuario/imagens"

# Garante que as pastas de dados existem
DATA_DIR.mkdir(parents=True, exist_ok=True)
CHROMA_DIR.mkdir(parents=True, exist_ok=True)
