"""
Publicador do Facebook (Graph API oficial da Meta).
Posta a foto na Página com legenda + hashtags no próprio texto.
"""
import requests

from src import config

API = "https://graph.facebook.com/v25.0"


class FacebookPublisher:
    plataforma = "facebook"

    def __init__(self, page_id=None, token=None, post_fn=None):
        self.page_id = page_id or config.FACEBOOK_PAGE_ID
        self.token = token or config.PAGE_ACCESS_TOKEN
        self._post_fn = post_fn

    def _post(self, url, params):
        if self._post_fn is not None:
            return self._post_fn(url, params)
        return requests.post(url, params=params, timeout=30).json()

    def publicar(self, image_url: str, legenda: str, hashtags: str = "") -> str:
        texto = f"{legenda}\n\n{hashtags}".strip()
        resp = self._post(
            f"{API}/{self.page_id}/photos",
            {"url": image_url, "message": texto, "access_token": self.token},
        )
        if "error" in resp:
            raise RuntimeError(f"Facebook: {resp['error'].get('message')}")
        return resp.get("post_id") or resp.get("id")
