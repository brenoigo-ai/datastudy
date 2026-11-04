"""Geração de identificadores únicos para entidades."""

from __future__ import annotations

import uuid


def novo_id() -> str:
    """Gera um identificador único (hex de um UUID4)."""

    return uuid.uuid4().hex
