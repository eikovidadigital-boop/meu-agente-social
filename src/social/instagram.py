"""
Publicador do Instagram (Graph API oficial da Meta).
Cria o container de mídia, publica e coloca as hashtags no primeiro comentário
(visual mais limpo, preferido pelo algoritmo).

Injeção de dependência: a chamada HTTP e o sleep podem ser substituídos em testes.
"""
import time

import requests

from src import config

API = "https://graph.facebook.com/v25.0"


class InstagramPublisher:
    plataforma = "instagram"

    def __init__(self, account_id=None, token=None, post_fn=None, sleep_fn=time.sleep):
        self.account_id = account_id or config.IG_ACCOUNT_ID
        self.token = token or config.PAGE_ACCESS_TOKEN
        self._post_fn = post_fn          # injetável p/ testes
        self._sleep = sleep_fn

    def _post(self, url, params):
        if self._post_fn is not None:
            return self._post_fn(url, params)
        return requests.post(url, params=params, timeout=30).json()

    def publicar(self, image_url: str, legenda: str, hashtags: str = "") -> str:
        # 1) cria o container
        container = self._post(
            f"{API}/{self.account_id}/media",
            {"image_url": image_url, "caption": legenda, "access_token": self.token},
        )
        if "error" in container:
            raise RuntimeError(f"Instagram container: {container['error'].get('message')}")

        # aguarda processamento do container
        self._sleep(8)

        # 2) publica
        pub = self._post(
            f"{API}/{self.account_id}/media_publish",
            {"creation_id": container["id"], "access_token": self.token},
        )
        if "error" in pub:
            raise RuntimeError(f"Instagram publish: {pub['error'].get('message')}")

        media_id = pub["id"]

        # 3) hashtags no primeiro comentário
        if hashtags:
            self._post(
                f"{API}/{media_id}/comments",
                {"message": hashtags, "access_token": self.token},
            )
        return media_id
