"""Contrato de persistência (Repository Pattern + DIP).

Toda a camada de `services` e de UI depende exclusivamente de
`Repository[T]` — nunca de `JsonFileRepository` ou `SqliteRepository`
diretamente. Isso é o que torna a "camada de persistência simulada"
facilmente substituível: trocar o backend é trocar qual classe
concreta a fábrica em `config.get_repository` instancia, sem tocar em
nenhum serviço.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class Repository(ABC, Generic[T]):
    """Operações mínimas de persistência (CRUD) para uma entidade `T`."""

    @abstractmethod
    def adicionar(self, entidade: T) -> T:
        """Persiste uma nova entidade e a retorna (já com `id`)."""

    @abstractmethod
    def obter(self, id: str) -> T | None:
        """Retorna a entidade com o `id` informado, ou `None`."""

    @abstractmethod
    def listar(self) -> list[T]:
        """Retorna todas as entidades armazenadas."""

    @abstractmethod
    def atualizar(self, entidade: T) -> T:
        """Substitui a entidade existente (mesmo `id`) pelos novos dados."""

    @abstractmethod
    def remover(self, id: str) -> None:
        """Remove a entidade com o `id` informado, se existir."""
