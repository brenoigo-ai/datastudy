"""Requisito 2 — Edital Verticalizado.

Interpretação adotada para "atualizando o progresso global
automaticamente sem necessidade de cadastro manual prévio": o usuário
não mantém um percentual por tópico à mão. Ele vincula um tópico-folha
a um `Conteudo` (via `conteudo_vinculado_id`); a partir daí, o
progresso nasce sozinho de `Conteudo.concluido` — que já é marcado como
parte do fluxo normal de estudo (`MateriaService.concluir_conteudo`).
Tópicos-pai herdam a média do progresso dos filhos, recursivamente.
"""

from __future__ import annotations

from datastudy.domain.models import Conteudo, Edital, TopicoEdital
from datastudy.repositories.base import Repository


class EditalService:
    def __init__(
        self,
        editais: Repository[Edital],
        topicos: Repository[TopicoEdital],
        conteudos: Repository[Conteudo],
    ) -> None:
        self._editais = editais
        self._topicos = topicos
        self._conteudos = conteudos

    def criar_edital(self, nome: str, orgao: str | None = None) -> Edital:
        return self._editais.adicionar(Edital(nome=nome, orgao=orgao))

    def listar_editais(self) -> list[Edital]:
        return self._editais.listar()

    def adicionar_topico(
        self,
        edital_id: str,
        nome: str,
        parent_id: str | None = None,
        conteudo_vinculado_id: str | None = None,
    ) -> TopicoEdital:
        topico = TopicoEdital(
            edital_id=edital_id,
            nome=nome,
            parent_id=parent_id,
            conteudo_vinculado_id=conteudo_vinculado_id,
        )
        return self._topicos.adicionar(topico)

    def listar_topicos(self, edital_id: str, parent_id: str | None = None) -> list[TopicoEdital]:
        """Filhos diretos de `parent_id` (ou tópicos raiz, se `None`)."""

        return [
            t
            for t in self._topicos.listar()
            if t.edital_id == edital_id and t.parent_id == parent_id
        ]

    def progresso(self, edital_id: str, parent_id: str | None = None) -> float:
        """Progresso de 0.0 a 1.0, calculado recursivamente:

        * Um tópico SEM filhos é uma folha: vale 1.0 se o `Conteudo`
          vinculado a ele estiver `concluido`, senão 0.0.
        * Um tópico COM filhos vale a média do progresso dos filhos.
        * Um edital sem nenhum tópico cadastrado vale 0.0 (evita
          divisão por zero).
        """

        filhos = self.listar_topicos(edital_id, parent_id)
        if not filhos:
            if parent_id is None:
                return 0.0  # edital ainda sem nenhum tópico
            topico = self._topicos.obter(parent_id)
            if topico is None or topico.conteudo_vinculado_id is None:
                return 0.0
            conteudo = self._conteudos.obter(topico.conteudo_vinculado_id)
            return 1.0 if (conteudo and conteudo.concluido) else 0.0
        return sum(self.progresso(edital_id, filho.id) for filho in filhos) / len(filhos)
