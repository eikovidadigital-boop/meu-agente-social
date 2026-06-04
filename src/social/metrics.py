"""
Coletor de métricas das publicações (Graph API oficial).
Busca curtidas, comentários e alcance de um post publicado.
Injeção de dependência: a chamada HTTP pode ser substituída em testes.
"""
import requests

from src import config

API = "https://graph.facebook.com/v25.0"


class MetricsCollector:
    def __init__(self, token=None, get_fn=None):
        self.token = token or config.PAGE_ACCESS_TOKEN
        self._get_fn = get_fn

    def _get(self, url, params):
        if self._get_fn is not None:
            return self._get_fn(url, params)
        return requests.get(url, params=params, timeout=30).json()

    def coletar(self, post_id_externo: str, plataforma: str = "instagram") -> dict:
        """Retorna {curtidas, comentarios, alcance} para o post."""
        if not post_id_externo:
            return {"curtidas": 0, "comentarios": 0, "alcance": 0}

        # curtidas e comentários (campos diretos da mídia)
        dados = self._get(
            f"{API}/{post_id_externo}",
            {"fields": "like_count,comments_count", "access_token": self.token},
        )
        curtidas = dados.get("like_count", 0) or 0
        comentarios = dados.get("comments_count", 0) or 0

        # alcance (via insights)
        alcance = 0
        insights = self._get(
            f"{API}/{post_id_externo}/insights",
            {"metric": "reach", "access_token": self.token},
        )
        try:
            alcance = insights["data"][0]["values"][0]["value"]
        except (KeyError, IndexError, TypeError):
            alcance = 0

        return {"curtidas": int(curtidas), "comentarios": int(comentarios), "alcance": int(alcance)}
