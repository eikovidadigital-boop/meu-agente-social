# -*- coding: utf-8 -*-
"""
Publicador do Instagram (Graph API). Cria container, publica e poe hashtags
no primeiro comentario. Agora aceita product_tags (Instagram Shopping) opcional.
Injecao de dependencia para testes (post_fn / sleep_fn).
"""
import json
import time

import requests

from src import config

API = "https://graph.facebook.com/v25.0"


class InstagramPublisher:
    plataforma = "instagram"

    def __init__(self, account_id=None, token=None, post_fn=None, sleep_fn=time.sleep):
        self.account_id = account_id or config.IG_ACCOUNT_ID
        self.token = token or config.PAGE_ACCESS_TOKEN
        self._post_fn = post_fn
        self._sleep = sleep_fn

    def _post(self, url, params):
        if self._post_fn is not None:
            return self._post_fn(url, params)
        return requests.post(url, params=params, timeout=30).json()

    def _container(self, image_url, legenda, product_tags):
        params = {"image_url": image_url, "caption": legenda, "access_token": self.token}
        if product_tags:
            params["product_tags"] = json.dumps(product_tags)
        return self._post(f"{API}/{self.account_id}/media", params)

    def publicar(self, image_url: str, legenda: str, hashtags: str = "", product_tags=None) -> str:
        # 1) cria o container (com etiqueta de produto, se houver)
        container = self._container(image_url, legenda, product_tags)
        if "error" in container and product_tags:
            # se a etiqueta falhar (ex.: permissao), publica sem ela
            print("aviso: etiqueta de produto falhou, publicando sem ela:",
                  container["error"].get("message"))
            container = self._container(image_url, legenda, None)
        if "error" in container:
            raise RuntimeError(f"Instagram container: {container['error'].get('message')}")

        self._sleep(8)

        # 2) publica
        pub = self._post(
            f"{API}/{self.account_id}/media_publish",
            {"creation_id": container["id"], "access_token": self.token},
        )
        if "error" in pub:
            raise RuntimeError(f"Instagram publish: {pub['error'].get('message')}")
        media_id = pub["id"]

        # 3) hashtags no primeiro comentario
        if hashtags:
            self._post(f"{API}/{media_id}/comments",
                       {"message": hashtags, "access_token": self.token})
        return media_id
