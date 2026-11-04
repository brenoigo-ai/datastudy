"""Requisito 7 — Planejamento e Ciclo de Estudos Inteligente.

Duas saídas, um único núcleo de ponderação:

* `gerar_planejamento`  -> distribui um total de horas disponíveis
  entre as matérias, proporcionalmente ao peso de cada uma.
* `gerar_ciclo_estudos` -> gera uma sequência intercalada e repetível
  de etapas (ex.: Matemática -> Biologia -> Física -> Matemática -> ...)
  em que matérias mais difíceis/importantes aparecem mais vezes, mas
  sempre intercaladas — nunca em rajada.

O ponto "inteligente" pedido no enunciado é resolvido com um algoritmo
real e testável (`RoundRobinPonderadoSuave`), não com heurísticas
arbitrárias.
"""

from __future__ import annotations

from datetime import date, timedelta

from datastudy.domain.enums import Dificuldade, PeriodoPlanejamento
from datastudy.domain.models import CicloEstudos, EtapaCiclo, Materia, MetaEstudo

_PESO_DIFICULDADE: dict[Dificuldade, float] = {
    Dificuldade.FACIL: 1.0,
    Dificuldade.MEDIA: 1.5,
    Dificuldade.DIFICIL: 2.0,
}


def peso_efetivo(materia: Materia, total_questoes_prova: int) -> float:
    """Combina peso declarado, dificuldade e proporção de questões da
    prova em um único peso — matérias mais difíceis, mais importantes
    (peso maior) ou com mais questões na prova recebem mais tempo de
    estudo e aparecem mais vezes no ciclo.

    `fator_questoes` é `1 + (questões_da_matéria / total_de_questões)`:
    uma matéria sem peso relativo em questões não perde espaço (fator
    mínimo 1), mas quem concentra mais questões ganha um bônus
    proporcional.
    """

    fator_dificuldade = _PESO_DIFICULDADE[materia.dificuldade]
    fator_questoes = 1.0
    if total_questoes_prova > 0 and materia.qtd_questoes_prova:
        fator_questoes = 1.0 + (materia.qtd_questoes_prova / total_questoes_prova)
    return max(materia.peso, 0.01) * fator_dificuldade * fator_questoes


def _pesos_normalizados(materias: list[Materia]) -> dict[str, float]:
    total_questoes = sum(m.qtd_questoes_prova or 0 for m in materias)
    return {m.id: peso_efetivo(m, total_questoes) for m in materias}


def gerar_planejamento(
    materias: list[Materia],
    horas_disponiveis: float,
    periodo: PeriodoPlanejamento = PeriodoPlanejamento.SEMANAL,
    inicio: date | None = None,
) -> list[MetaEstudo]:
    """Planejamento de Estudos: reparte `horas_disponiveis` entre as
    matérias proporcionalmente ao peso efetivo de cada uma."""

    if not materias:
        return []
    pesos = _pesos_normalizados(materias)
    soma = sum(pesos.values()) or 1.0
    inicio = inicio or date.today()
    dias = 7 if periodo == PeriodoPlanejamento.SEMANAL else 30
    fim = inicio + timedelta(days=dias - 1)
    return [
        MetaEstudo(
            materia_id=m.id,
            periodo=periodo,
            horas_meta=round(horas_disponiveis * (pesos[m.id] / soma), 2),
            inicio=inicio,
            fim=fim,
        )
        for m in materias
    ]


class RoundRobinPonderadoSuave:
    """Smooth Weighted Round Robin (SWRR) — a mesma técnica usada por
    balanceadores de carga (ex.: o algoritmo de upstream do Nginx) para
    distribuir itens proporcionalmente ao peso, porém intercalados.

    Diferente de um agrupamento ingênuo (que geraria algo como
    "AAABC", concentrando repetições da mesma matéria em sequência), o
    SWRR produz algo como "AABAAC..." — o que bate com o comportamento
    descrito no app de referência ("as matérias planejadas vão se
    alternando uma após a outra").

    Funcionamento: cada chave acumula seu próprio peso a cada rodada;
    escolhe-se sempre quem tem o maior acumulado, e subtrai-se o total
    de pesos do escolhido — isso garante que ninguém "monopoliza" runs
    consecutivos mesmo tendo peso bem maior que os demais.
    """

    def __init__(self, pesos: dict[str, float]) -> None:
        if not pesos:
            raise ValueError("é preciso ao menos uma matéria para montar o ciclo")
        self._pesos = pesos
        self._atual = {chave: 0.0 for chave in pesos}
        self._total = sum(pesos.values())

    def proximo(self) -> str:
        for chave in self._atual:
            self._atual[chave] += self._pesos[chave]
        escolhido = max(self._atual, key=self._atual.get)
        self._atual[escolhido] -= self._total
        return escolhido


def gerar_ciclo_estudos(
    materias: list[Materia],
    duracao_etapa_minutos: int = 60,
    tamanho_ciclo: int | None = None,
) -> CicloEstudos:
    """Ciclo de Estudos: gera `tamanho_ciclo` etapas (padrão: 3x o
    número de matérias) intercalando-as via `RoundRobinPonderadoSuave`.
    """

    if not materias:
        return CicloEstudos(etapas=[])
    pesos = _pesos_normalizados(materias)
    swrr = RoundRobinPonderadoSuave(pesos)
    tamanho = tamanho_ciclo or max(len(materias) * 3, 6)
    etapas = [
        EtapaCiclo(materia_id=swrr.proximo(), duracao_minutos=duracao_etapa_minutos)
        for _ in range(tamanho)
    ]
    return CicloEstudos(etapas=etapas)
