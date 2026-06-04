"""
Gerador de Imagens.
Cria a imagem com gpt-image-1 (img2img a partir da foto do produto, quando
disponível) e hospeda no ImgBB, devolvendo uma URL pública pronta para postar.

Injeção de dependência: as chamadas externas podem ser substituídas em testes.
"""
import requests

from src import config

OPENAI_EDITS = "https://api.openai.com/v1/images/edits"
OPENAI_GENERATIONS = "https://api.openai.com/v1/images/generations"
IMGBB_UPLOAD = "https://api.imgbb.com/1/upload"


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
        """Hospeda o base64 no ImgBB e retorna a URL pública."""
        if self._hospedar_fn is not None:
            return self._hospedar_fn(b64=b64)

        resp = requests.post(
            IMGBB_UPLOAD,
            data={"key": config.IMGBB_API_KEY, "image": b64},
            timeout=60,
        )
        dados = resp.json()
        if not dados.get("success"):
            raise RuntimeError(f"Erro ImgBB: {dados}")
        return dados["data"]["url"]

    def criar(self, prompt: str, produto_img_url: str = None) -> str:
        """Fluxo completo: prompt -> imagem -> URL pública."""
        b64 = self.gerar(prompt, produto_img_url)
        return self.hospedar(b64)
