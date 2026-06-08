# -*- coding: utf-8 -*-
"""Chamadas HTTP com retry automatico (falhas de rede / erros 5xx temporarios)."""
import time
import requests


def _try(fn, *a, tentativas=3, espera=5, **kw):
    erro = None
    for i in range(tentativas):
        try:
            r = fn(*a, **kw)
            sc = getattr(r, "status_code", 200)
            if sc and sc >= 500:                 # erro temporario do servidor
                raise RuntimeError(f"HTTP {sc}")
            return r
        except Exception as e:
            erro = e
            if i < tentativas - 1:
                time.sleep(espera * (i + 1))      # espera crescente: 5s, 10s...
    raise erro


def get(*a, **kw):
    return _try(requests.get, *a, **kw)


def post(*a, **kw):
    return _try(requests.post, *a, **kw)


def put(*a, **kw):
    return _try(requests.put, *a, **kw)
