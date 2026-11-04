"""Requisitos 5 e 6 — Dashboard/Gráficos e Registro de Exercícios.

Este serviço só agrega dados (nenhuma regra de UI); os gráficos em si
ficam em `pages/5_📊_Desempenho.py`, para manter a lógica testável sem
precisar de um navegador."""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import date

from datastudy.domain.models import AtividadeEstudo, RegistroExercicio
from datastudy.repositories.base import Repository


class DesempenhoService:
    def __init__(self, registros: Repository[RegistroExercicio]) -> None:
        self._registros = registros

    def taxa_acerto_geral(self) -> float:
        registros = self._registros.listar()
        total = sum(r.quantidade for r in registros)
        acertos = sum(r.acertos for r in registros)
        return round((acertos / total) * 100, 1) if total else 0.0

    def taxa_acerto_por_materia(self) -> dict[str, float]:
        por_materia: dict[str, list[RegistroExercicio]] = defaultdict(list)
        for registro in self._registros.listar():
            por_materia[registro.materia_id].append(registro)
        resultado: dict[str, float] = {}
        for materia_id, registros in por_materia.items():
            total = sum(r.quantidade for r in registros)
            acertos = sum(r.acertos for r in registros)
            resultado[materia_id] = round((acertos / total) * 100, 1) if total else 0.0
        return resultado

    def totais(self) -> dict[str, int]:
        registros = self._registros.listar()
        return {
            "questoes": sum(r.quantidade for r in registros),
            "acertos": sum(r.acertos for r in registros),
        }


def tempo_por_tipo_estudo(atividades: list[AtividadeEstudo]) -> Counter[str]:
    """Conta atividades por `TipoEstudo` (para o gráfico de pizza de
    "Tipo de Estudo" — leitura vs. exercício vs. revisão etc.)."""

    return Counter(a.tipo_estudo.value for a in atividades)


def linha_do_tempo(
    atividades: list[AtividadeEstudo],
) -> dict[date, float]:
    """Horas líquidas totais por dia (para comparar produtividade entre
    períodos)."""

    por_dia: dict[date, float] = defaultdict(float)
    for atividade in atividades:
        dia = atividade.iniciado_em.date()
        por_dia[dia] += atividade.duracao_liquida().total_seconds() / 3600
    return dict(sorted(por_dia.items()))
