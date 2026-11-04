"""Implementação de `Repository` sobre SQLite.

Usa uma tabela genérica `(id TEXT PRIMARY KEY, dados TEXT)` por
entidade, guardando cada registro como um JSON serializado pelo
pydantic. Isso evita migração de schema por entidade — o "schema" real
continua vivendo nos modelos pydantic, não no banco — e é o que torna
possível oferecer exatamente a mesma interface do
`JsonFileRepository`: trocar de backend é só mudar
`DATASTUDY_BACKEND=sqlite` (ver `config.py`).

Suporta concorrência entre processos razoavelmente bem (cada operação
abre/fecha sua própria conexão), o que o backend em arquivo JSON não
oferece.
"""

from __future__ import annotations

import sqlite3
import threading
from pathlib import Path
from typing import Generic, Type, TypeVar

from pydantic import BaseModel

from datastudy.repositories.base import Repository

T = TypeVar("T", bound=BaseModel)


class SqliteRepository(Repository[T], Generic[T]):
    def __init__(self, banco: Path, modelo: Type[T], tabela: str | None = None) -> None:
        self._banco = banco
        self._modelo = modelo
        self._tabela = tabela or modelo.__name__.lower()
        self._lock = threading.Lock()
        banco.parent.mkdir(parents=True, exist_ok=True)
        with self._conectar() as conexao:
            conexao.execute(
                f"CREATE TABLE IF NOT EXISTS {self._tabela} "
                "(id TEXT PRIMARY KEY, dados TEXT NOT NULL)"
            )

    def _conectar(self) -> sqlite3.Connection:
        return sqlite3.connect(self._banco)

    def adicionar(self, entidade: T) -> T:
        with self._lock, self._conectar() as conexao:
            conexao.execute(
                f"INSERT INTO {self._tabela} (id, dados) VALUES (?, ?)",
                (entidade.id, entidade.model_dump_json()),
            )
        return entidade

    def obter(self, id: str) -> T | None:
        with self._conectar() as conexao:
            linha = conexao.execute(
                f"SELECT dados FROM {self._tabela} WHERE id = ?", (id,)
            ).fetchone()
        return self._modelo.model_validate_json(linha[0]) if linha else None

    def listar(self) -> list[T]:
        with self._conectar() as conexao:
            linhas = conexao.execute(f"SELECT dados FROM {self._tabela}").fetchall()
        return [self._modelo.model_validate_json(l[0]) for l in linhas]

    def atualizar(self, entidade: T) -> T:
        with self._lock, self._conectar() as conexao:
            cursor = conexao.execute(
                f"UPDATE {self._tabela} SET dados = ? WHERE id = ?",
                (entidade.model_dump_json(), entidade.id),
            )
            if cursor.rowcount == 0:
                raise ValueError(
                    f"Entidade com id={entidade.id!r} não encontrada em {self._tabela}"
                )
        return entidade

    def remover(self, id: str) -> None:
        with self._lock, self._conectar() as conexao:
            conexao.execute(f"DELETE FROM {self._tabela} WHERE id = ?", (id,))
