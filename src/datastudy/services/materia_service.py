"""Requisito 1 — Gestão Core: cadastro hierárquico de Matérias e
Conteúdos (uma Matéria tem N Conteúdos)."""

from __future__ import annotations

from datastudy.domain.models import Conteudo, Materia
from datastudy.repositories.base import Repository


class MateriaService:
    def __init__(
        self, materias: Repository[Materia], conteudos: Repository[Conteudo]
    ) -> None:
        self._materias = materias
        self._conteudos = conteudos

    # -- Matérias ----------------------------------------------------
    def criar_materia(self, nome: str, **kwargs) -> Materia:
        return self._materias.adicionar(Materia(nome=nome, **kwargs))

    def listar_materias(self) -> list[Materia]:
        return self._materias.listar()

    def remover_materia(self, materia_id: str) -> None:
        """Remove a matéria e, em cascata, seus conteúdos (evita
        conteúdos "órfãos" apontando para uma matéria inexistente)."""

        for conteudo in self.listar_conteudos(materia_id):
            self._conteudos.remover(conteudo.id)
        self._materias.remover(materia_id)

    # -- Conteúdos -----------------------------------------------------
    def adicionar_conteudo(self, materia_id: str, nome: str) -> Conteudo:
        if self._materias.obter(materia_id) is None:
            raise ValueError(f"Matéria {materia_id!r} não encontrada")
        return self._conteudos.adicionar(Conteudo(materia_id=materia_id, nome=nome))

    def listar_conteudos(self, materia_id: str) -> list[Conteudo]:
        return [c for c in self._conteudos.listar() if c.materia_id == materia_id]

    def concluir_conteudo(self, conteudo_id: str, concluido: bool = True) -> Conteudo:
        conteudo = self._conteudos.obter(conteudo_id)
        if conteudo is None:
            raise ValueError(f"Conteúdo {conteudo_id!r} não encontrado")
        conteudo.concluido = concluido
        return self._conteudos.atualizar(conteudo)
