"""Implementação de `Repository` sobre um arquivo JSON simples.

Adequada para uso local/single-user (é o backend padrão do DataStudy).
Não é seguro para escrita concorrente entre *processos* distintos —
o `threading.Lock` protege apenas contra corrida entre threads do
mesmo processo. Para múltiplos processos/usuários, use
`SqliteRepository` (mesma interface, troca transparente).
"""

from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Generic, Type, TypeVar

from pydantic import BaseModel

from datastudy.repositories.base import Repository

T = TypeVar("T", bound=BaseModel)


class JsonFileRepository(Repository[T], Generic[T]):
    def __init__(self, arquivo: Path, modelo: Type[T]) -> None:
        self._arquivo = arquivo
        self._modelo = modelo
        self._lock = threading.Lock()
        self._arquivo.parent.mkdir(parents=True, exist_ok=True)
        if not self._arquivo.exists():
            self._arquivo.write_text("[]", encoding="utf-8")

    def _ler_todos(self) -> list[dict]:
        conteudo = self._arquivo.read_text(encoding="utf-8") or "[]"
        return json.loads(conteudo)

    def _salvar_todos(self, registros: list[dict]) -> None:
        self._arquivo.write_text(
            json.dumps(registros, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    def adicionar(self, entidade: T) -> T:
        with self._lock:
            registros = self._ler_todos()
            registros.append(json.loads(entidade.model_dump_json()))
            self._salvar_todos(registros)
        return entidade

    def obter(self, id: str) -> T | None:
        for registro in self._ler_todos():
            if registro.get("id") == id:
                return self._modelo.model_validate(registro)
        return None

    def listar(self) -> list[T]:
        return [self._modelo.model_validate(r) for r in self._ler_todos()]

    def atualizar(self, entidade: T) -> T:
        with self._lock:
            registros = self._ler_todos()
            for i, registro in enumerate(registros):
                if registro.get("id") == entidade.id:
                    registros[i] = json.loads(entidade.model_dump_json())
                    break
            else:
                raise ValueError(
                    f"Entidade com id={entidade.id!r} não encontrada em {self._arquivo.name}"
                )
            self._salvar_todos(registros)
        return entidade

    def remover(self, id: str) -> None:
        with self._lock:
            registros = [r for r in self._ler_todos() if r.get("id") != id]
            self._salvar_todos(registros)
