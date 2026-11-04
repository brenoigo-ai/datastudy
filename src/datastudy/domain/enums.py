"""Enumerações do domínio DataStudy.

Mantidas como `str, Enum` para serializar como texto simples em JSON
(tanto no `JsonFileRepository` quanto no `SqliteRepository`), sem
precisar de conversores customizados no pydantic.
"""

from __future__ import annotations

from enum import Enum


class Dificuldade(str, Enum):
    """Dificuldade declarada de uma matéria — usada pelo algoritmo de
    ponderação em `services.planning_service`."""

    FACIL = "facil"
    MEDIA = "media"
    DIFICIL = "dificil"


class TipoEstudo(str, Enum):
    """Classifica o tipo de atividade, espelhando o pacote "Registro de
    Exercícios + Tipo de Estudo" do app de referência (Aprovado), para
    alimentar o gráfico de distribuição de tempo por tipo."""

    LEITURA = "leitura"
    EXERCICIO = "exercicio"
    REVISAO = "revisao"
    VIDEO_AULA = "video_aula"
    SALA_DE_AULA = "sala_de_aula"
    RESUMO = "resumo"
    MAPA_MENTAL = "mapa_mental"
    FLASH_CARDS = "flash_cards"
    AUDIO = "audio"
    OUTRO = "outro"


class StatusAtividade(str, Enum):
    """Estado do cronômetro de uma `AtividadeEstudo`."""

    EM_ANDAMENTO = "em_andamento"
    PAUSADA = "pausada"
    CONCLUIDA = "concluida"


class TipoAgendamentoRevisao(str, Enum):
    """As três estratégias de repetição espaçada suportadas."""

    PERIODICA = "periodica"          # intervalos de dias fixos (1, 7, 30...)
    DIA_DA_SEMANA = "dia_da_semana"  # um dia fixo, repetido a cada N semanas
    ADAPTATIVA = "adaptativa"        # SM-2: o intervalo é recalculado a cada revisão


class PeriodoPlanejamento(str, Enum):
    """Granularidade de uma meta no Planejamento de Estudos."""

    SEMANAL = "semanal"
    MENSAL = "mensal"
