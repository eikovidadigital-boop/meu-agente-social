"""
Orquestrador de publicação.
Lê as publicações pendentes do banco, posta na plataforma certa e atualiza
o status. Inclui proteção anti-banimento (jitter e intervalo entre redes).
"""
import random
import time

from src.storage import db


class Publisher:
    def __init__(self, adapters, sleep_fn=time.sleep, jitter=True):
        # adapters: lista de publicadores (cada um com atributo .plataforma)
        self.adapters = {a.plataforma: a for a in adapters}
        self._sleep = sleep_fn
        self.jitter = jitter

    def _texto_para(self, plataforma, conteudo):
        """Instagram usa hashtags no comentário (separadas); Facebook no texto."""
        return conteudo.get("legenda", ""), conteudo.get("hashtags", "")

    def publicar_pendentes(self) -> list[dict]:
        resultados = []
        pendentes = db.publicacoes_pendentes()

        for i, pub in enumerate(pendentes):
            plataforma = pub["plataforma"]
            adapter = self.adapters.get(plataforma)
            if adapter is None:
                db.marcar_erro(pub["id"], f"sem adapter para {plataforma}")
                resultados.append({"id": pub["id"], "status": "erro", "motivo": "sem adapter"})
                continue

            conteudo = db.obter_conteudo(pub["conteudo_id"])
            if not conteudo:
                db.marcar_erro(pub["id"], "conteúdo não encontrado")
                resultados.append({"id": pub["id"], "status": "erro", "motivo": "sem conteúdo"})
                continue

            legenda, hashtags = self._texto_para(plataforma, conteudo)

            # Anti-ban: intervalo entre publicações (exceto antes da primeira)
            if self.jitter and i > 0:
                self._sleep(random.randint(30, 90))

            try:
                post_id = adapter.publicar(conteudo.get("imagem_url", ""), legenda, hashtags)
                db.marcar_publicado(pub["id"], post_id)
                resultados.append({"id": pub["id"], "status": "ok", "post_id": post_id})
            except Exception as exc:  # noqa: BLE001
                db.marcar_erro(pub["id"], exc)
                resultados.append({"id": pub["id"], "status": "erro", "motivo": str(exc)})

        return resultados
