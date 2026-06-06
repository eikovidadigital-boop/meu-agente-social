"""
Gerador de Imagens.
Cria a imagem com gpt-image-1 (img2img a partir da foto do produto, quando
disponível) e hospeda no GitHub (repo público), devolvendo uma URL
raw.githubusercontent.com que o Instagram aceita. Não depende de cadastro
em serviços de imagem (que costumam bloquear contas/servidores).

Injeção de dependência: as chamadas externas podem ser substituídas em testes.
"""
import time

import requests

from src import config

OPENAI_EDITS = "https://api.openai.com/v1/images/edits"
OPENAI_GENERATIONS = "https://api.openai.com/v1/images/generations"


class ImageGenerator:
    def __init__(self, gerar_fn=None, hospedar_fn=None):
        # funções injetáveis para teste (substituem as chamadas reais)
        self._gerar_fn = gerar_fn
        self._hospedar_fn = hospedar_fn

    def gerar(self, prompt: str, produto_img_url: str = None) -> str:
        """Gera a imagem e retorna o conteúdo em base64."""
        if self._gerar_fn is not None:
            return self._gerar_fn(prompt=prompt, produto_img_url=produto_img_url)

        if produto_img_url:
            # img2img: usa a foto real do produto como base
            img = requests.get(produto_img_url, timeout=30)
            img.raise_for_status()
            resp = requests.post(
                OPENAI_EDITS,
                headers={"Authorization": f"Bearer {config.OPENAI_API_KEY}"},
                files={"image": ("produto.png", img.content, "image/png")},
                data={"model": "gpt-image-1", "prompt": prompt, "size": "1024x1024",
                      "n": "1", "output_format": "jpeg"},
                timeout=120,
            )
        else:
            # text2img: gera do zero
            resp = requests.post(
                OPENAI_GENERATIONS,
                headers={"Authorization": f"Bearer {config.OPENAI_API_KEY}",
                         "Content-Type": "application/json"},
                json={"model": "gpt-image-1", "prompt": prompt, "size": "1024x1024",
                      "n": 1, "output_format": "jpeg"},
                timeout=120,
            )

        dados = resp.json()
        if "error" in dados:
            raise RuntimeError(f"Erro gpt-image-1: {dados['error'].get('message', dados['error'])}")
        return dados["data"][0]["b64_json"]

    def hospedar(self, b64: str) -> str:
        """Sobe a imagem num repo público do GitHub e retorna a URL raw (aceita pelo Instagram)."""
        if self._hospedar_fn is not None:
            return self._hospedar_fn(b64=b64)

        nome = f"img_{int(time.time())}.jpg"
        api = f"https://api.github.com/repos/{config.GH_IMAGES_REPO}/contents/{nome}"
        resp = requests.put(
            api,
            headers={
                "Authorization": f"token {config.GH_TOKEN}",
                "Accept": "application/vnd.github+json",
            },
            json={"message": f"imagem {nome}", "content": b64},
            timeout=60,
        )
        dados = resp.json()
        if "content" not in dados:
            raise RuntimeError(f"Erro GitHub host: {dados}")
        return f"https://raw.githubusercontent.com/{config.GH_IMAGES_REPO}/main/{nome}"

    def criar(self, prompt: str, produto_img_url: str = None) -> str:
        """Fluxo completo: prompt -> imagem -> URL pública."""
        b64 = self.gerar(prompt, produto_img_url)
        return self.hospedar(b64)

    def montar_com_cenario(self, produto_bytes: bytes, indice: int = 0,
                           usar_ia_recorte: bool = True) -> str:
        """
        Monta o post: recorta o produto REAL, gera um CENÁRIO com IA (sem produto),
        junta os dois com um layout que rotaciona, hospeda e devolve a URL.
        O produto nunca é alterado — só o cenário é gerado.
        """
        import base64
        import io

        from PIL import Image

        from src.image import composer

        # 1) recorta o produto real (rótulo preservado)
        recorte = composer.recortar_produto(produto_bytes, usar_ia=usar_ia_recorte)
        # 2) gera só o cenário (texto -> imagem, sem produto)
        cenario_prompt = composer.escolher_cenario(indice)
        b64_fundo = self.gerar(cenario_prompt)  # text2img
        fundo = Image.open(io.BytesIO(base64.b64decode(b64_fundo)))
        # 3) junta com o layout do dia
        layout = composer.escolher_layout(indice)
        jpeg = composer.compor(recorte, fundo, layout)
        # 4) hospeda e devolve a URL
        return self.hospedar(base64.b64encode(jpeg).decode())

