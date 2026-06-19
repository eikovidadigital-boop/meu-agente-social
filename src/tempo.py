# -*- coding: utf-8 -*-
"""
Relogio do sistema em horario de Brasilia (BRT, UTC-3 fixo — o Brasil nao tem
mais horario de verao desde 2019). Usar isto em vez de datetime.now() garante
que a rotacao, o modo do dia (educativo/conversao) e os relatorios fiquem
sempre alinhados ao publico brasileiro, mesmo o servidor rodando em UTC.
"""
from datetime import datetime, timezone, timedelta

BRT = timezone(timedelta(hours=-3))


def agora():
    """datetime atual em horario de Brasilia."""
    return datetime.now(BRT)


def hoje_str():
    return agora().strftime("%Y-%m-%d")


def mes_ref(dt=None):
    """Ano-mes de referencia (ex.: '2026-06')."""
    return (dt or agora()).strftime("%Y-%m")
