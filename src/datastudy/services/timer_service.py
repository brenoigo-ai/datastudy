"""Requisitos 3 e 4 — Tracking de tempo (Iniciar/Pausar/Concluir com
horas líquidas) e Gestão de Foco Ativa (sugestão de descanso ativo ao
pausar, em vez de deixar o cronômetro ocioso indefinidamente)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from datastudy.domain.enums import StatusAtividade, TipoEstudo
from datastudy.domain.models import AtividadeEstudo, IntervaloPausa
from datastudy.repositories.base import Repository


@dataclass(frozen=True)
class SugestaoDescanso:
    """Sugestão de pausa ativa exibida assim que o cronômetro é
    pausado — é a resposta direta ao problema descrito no projeto
    DataStudy ("o cronômetro fica pausado indefinidamente, sem
    orientação sobre o tempo de descanso")."""

    respiracao: str
    alongamento: str
    duracao_sugerida_segundos: int = 90


# Listas propositalmente pequenas e roteadas por índice (não por
# aleatoriedade) para que a sugestão seja determinística e testável,
# mas ainda assim varie a cada nova pausa.
_EXERCICIOS_RESPIRACAO: tuple[str, ...] = (
    "Respiração 4-7-8: inspire pelo nariz em 4 segundos, segure por 7 "
    "segundos e expire lentamente pela boca em 8 segundos. Repita 3 vezes.",
    "Respiração quadrada: inspire em 4 segundos, segure 4, expire em 4 "
    "e segure mais 4 com os pulmões vazios. Repita 4 vezes.",
    "Respiração diafragmática: uma mão no peito e outra na barriga; "
    "inspire deixando a barriga (não o peito) subir, e expire bem devagar.",
)

_EXERCICIOS_ALONGAMENTO: tuple[str, ...] = (
    "Gire lentamente o pescoço para os dois lados e incline a cabeça em "
    "direção a cada ombro, segurando 10 segundos de cada lado.",
    "Levante os braços acima da cabeça, entrelace os dedos e estique a "
    "coluna para cima, como se fosse tocar o teto.",
    "Em pé, apoie as mãos na cintura e gire o tronco suavemente para "
    "cada lado, alongando a lombar.",
    "Estenda um braço à frente e puxe os dedos para trás com a outra "
    "mão, alongando o antebraço; repita no outro braço.",
)


def sugerir_descanso(numero_da_pausa: int) -> SugestaoDescanso:
    """Roda pelas listas de exercícios conforme o número da pausa (a
    N-ésima pausa desta atividade), para não repetir sempre a mesma
    sugestão."""

    return SugestaoDescanso(
        respiracao=_EXERCICIOS_RESPIRACAO[numero_da_pausa % len(_EXERCICIOS_RESPIRACAO)],
        alongamento=_EXERCICIOS_ALONGAMENTO[numero_da_pausa % len(_EXERCICIOS_ALONGAMENTO)],
    )


class TimerService:
    """Controla o ciclo de vida de uma `AtividadeEstudo`."""

    def __init__(self, atividades: Repository[AtividadeEstudo]) -> None:
        self._atividades = atividades

    def iniciar(
        self, materia_id: str, conteudo_id: str | None, tipo_estudo: TipoEstudo
    ) -> AtividadeEstudo:
        atividade = AtividadeEstudo(
            materia_id=materia_id, conteudo_id=conteudo_id, tipo_estudo=tipo_estudo
        )
        return self._atividades.adicionar(atividade)

    def pausar(self, atividade_id: str) -> tuple[AtividadeEstudo, SugestaoDescanso]:
        atividade = self._obter_em_andamento(atividade_id)
        atividade.status = StatusAtividade.PAUSADA
        atividade.pausas.append(IntervaloPausa(inicio=datetime.now()))
        atividade = self._atividades.atualizar(atividade)
        return atividade, sugerir_descanso(len(atividade.pausas) - 1)

    def retomar(self, atividade_id: str) -> AtividadeEstudo:
        atividade = self._atividades.obter(atividade_id)
        if atividade is None or atividade.status != StatusAtividade.PAUSADA:
            raise ValueError("Atividade não está pausada")
        atividade.pausas[-1].fim = datetime.now()
        atividade.status = StatusAtividade.EM_ANDAMENTO
        return self._atividades.atualizar(atividade)

    def concluir(self, atividade_id: str) -> AtividadeEstudo:
        atividade = self._atividades.obter(atividade_id)
        if atividade is None:
            raise ValueError("Atividade não encontrada")
        if atividade.pausas and atividade.pausas[-1].fim is None:
            atividade.pausas[-1].fim = datetime.now()
        atividade.status = StatusAtividade.CONCLUIDA
        atividade.finalizado_em = datetime.now()
        return self._atividades.atualizar(atividade)

    def _obter_em_andamento(self, atividade_id: str) -> AtividadeEstudo:
        atividade = self._atividades.obter(atividade_id)
        if atividade is None or atividade.status != StatusAtividade.EM_ANDAMENTO:
            raise ValueError("Atividade não está em andamento")
        return atividade
