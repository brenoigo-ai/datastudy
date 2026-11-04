"""Configuração e fábrica de repositórios do DataStudy.

`get_repository` é o único ponto do sistema que sabe qual backend de
persistência concreto existe. Serviços e páginas Streamlit só
enxergam `Repository[T]` (ver `repositories/base.py`) — a troca de
backend (JSON <-> SQLite, e no futuro um banco remoto) é uma mudança
de configuração, não de código.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Type, TypeVar

from pydantic import BaseModel

from datastudy.repositories.base import Repository
from datastudy.repositories.json_repository import JsonFileRepository
from datastudy.repositories.sqlite_repository import SqliteRepository

T = TypeVar("T", bound=BaseModel)

# Raiz do projeto (três níveis acima deste arquivo: src/datastudy/config.py -> raiz)
BASE_DIR = Path(__file__).resolve().parent.parent.parent

#: Diretório onde os dados são gravados. Sobrescrevível via variável de
#: ambiente — os testes usam isso para isolar cada execução em um
#: diretório temporário.
DATA_DIR = Path(os.getenv("DATASTUDY_DATA_DIR", str(BASE_DIR / "data")))

#: "json" (padrão) ou "sqlite".
BACKEND = os.getenv("DATASTUDY_BACKEND", "json").lower()


def get_repository(modelo: Type[T], nome: str | None = None) -> Repository[T]:
    """Devolve o repositório configurado para `modelo`.

    `nome` controla o nome do arquivo/tabela; por padrão usa o nome da
    classe em minúsculas (ex.: `Materia` -> `materia.json` / tabela
    `materia`).
    """

    nome = nome or modelo.__name__.lower()
    if BACKEND == "sqlite":
        return SqliteRepository(DATA_DIR / "datastudy.db", modelo, tabela=nome)
    return JsonFileRepository(DATA_DIR / f"{nome}.json", modelo)
