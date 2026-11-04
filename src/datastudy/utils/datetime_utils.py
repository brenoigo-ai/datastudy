"""Utilidades de data/hora sem regra de negócio."""

from __future__ import annotations

from datetime import timedelta


def formatar_duracao(duracao: timedelta) -> str:
    """Formata uma duração como "1h 25m 3s", "25m 3s" ou "3s"."""

    total_segundos = max(int(duracao.total_seconds()), 0)
    horas, resto = divmod(total_segundos, 3600)
    minutos, segundos = divmod(resto, 60)
    if horas:
        return f"{horas}h {minutos}m {segundos}s"
    if minutos:
        return f"{minutos}m {segundos}s"
    return f"{segundos}s"
