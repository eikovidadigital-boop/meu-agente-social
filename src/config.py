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

# RAG
CHUNK_TAMANHO = 500          # tamanho alvo de cada chunk (em palavras aproximadas)
CHUNK_SOBREPOSICAO = 50      # sobreposição entre chunks (mantém contexto)
BUSCA_TOP_K = 5              # quantos trechos a busca retorna

# Credenciais externas (preenchidas via ambiente/GitHub Secrets)
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
IMGBB_API_KEY = os.environ.get("IMGBB_API_KEY", "")
IG_ACCOUNT_ID = os.environ.get("IG_ACCOUNT_ID", "")
FACEBOOK_PAGE_ID = os.environ.get("FACEBOOK_PAGE_ID", "")
PAGE_ACCESS_TOKEN = os.environ.get("PAGE_ACCESS_TOKEN", "")

# Cloudinary (host de imagem que o Instagram aceita; upload assinado)
CLOUDINARY_CLOUD_NAME = os.environ.get("CLOUDINARY_CLOUD_NAME", "")
CLOUDINARY_API_KEY = os.environ.get("CLOUDINARY_API_KEY", "")
CLOUDINARY_API_SECRET = os.environ.get("CLOUDINARY_API_SECRET", "")

# Garante que as pastas de dados existem
DATA_DIR.mkdir(parents=True, exist_ok=True)
CHROMA_DIR.mkdir(parents=True, exist_ok=True)
