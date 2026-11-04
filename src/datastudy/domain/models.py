"""Entidades de domínio do DataStudy.

Usamos `pydantic.BaseModel` em vez de `dataclasses` puros por um motivo
pragmático e deliberado: precisamos (de)serializar para JSON em duas
implementações de repositório diferentes (arquivo e SQLite) e validar
dados vindos da UI. O pydantic resolve os dois problemas com
`model_dump_json()` / `model_validate_json()`, sem código repetido de
serialização manual em cada entidade.

Isso acopla o domínio ao pydantic (uma biblioteca "core", não a uma
tecnologia de armazenamento específica) — é a troca consciente que o
enunciado do projeto pede ("camada de persistência... facilmente
substituível"): o que é fixo é o contrato `Repository[T]`
(`repositories/base.py`); o backend concreto (JSON hoje, SQLite ou um
banco remoto amanhã) é 100% substituível sem tocar aqui.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from datastudy.domain.enums import (
    Dificuldade,
    PeriodoPlanejamento,
    StatusAtividade,
    TipoAgendamentoRevisao,
    TipoEstudo,
)
from datastudy.utils.ids import novo_id


class EntidadeBase(BaseModel):
    """Base para toda entidade persistível: garante um `id` único e
    proíbe campos não declarados (evita erros silenciosos de digitação
    vindos da UI ou de dados antigos)."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(default_factory=novo_id)


# --------------------------------------------------------------------------
# 1. Gestão core — Matérias e Conteúdos
# --------------------------------------------------------------------------


class Materia(EntidadeBase):
    """Uma disciplina/matéria de estudo.

    `peso`, `dificuldade` e `qtd_questoes_prova` alimentam o algoritmo
    de ponderação em `services.planning_service.peso_efetivo`.
    """

    nome: str
    cor: str = "#4C6EF5"
    dificuldade: Dificuldade = Dificuldade.MEDIA
    peso: float = Field(default=1.0, gt=0)
    qtd_questoes_prova: Optional[int] = Field(default=None, ge=0)


class Conteudo(EntidadeBase):
    """Um tópico dentro de uma matéria (ex.: "Princípios do Direito
    Penal"). `concluido` é a única fonte de verdade usada pelo cálculo
    automático de progresso do edital — ver `EditalService.progresso`.
    """

    materia_id: str
    nome: str
    concluido: bool = False


# --------------------------------------------------------------------------
# 2. Edital verticalizado
# --------------------------------------------------------------------------


class Edital(EntidadeBase):
    """Um edital/concurso acompanhado de forma hierárquica."""

    nome: str
    orgao: Optional[str] = None


class TopicoEdital(EntidadeBase):
    """Nó da árvore de um edital.

    `parent_id=None` marca um tópico raiz. Um tópico-folha pode apontar
    para um `Conteudo` via `conteudo_vinculado_id`; o progresso desse
    tópico passa a refletir automaticamente `Conteudo.concluido`, sem
    que o usuário precise digitar um percentual manualmente.
    """

    edital_id: str
    nome: str
    parent_id: Optional[str] = None
    conteudo_vinculado_id: Optional[str] = None


# --------------------------------------------------------------------------
# 3/4. Tracking de tempo + Gestão de foco ativa
# --------------------------------------------------------------------------


class IntervaloPausa(BaseModel):
    """Um intervalo de pausa dentro de uma atividade. `fim=None`
    significa "ainda em pausa"."""

    inicio: datetime
    fim: Optional[datetime] = None

    def duracao(self, agora: Optional[datetime] = None) -> timedelta:
        fim = self.fim or (agora or datetime.now())
        return fim - self.inicio


class AtividadeEstudo(EntidadeBase):
    """Uma sessão de estudo cronometrada.

    A duração líquida (o que o app de referência chama de "horas
    líquidas") é bruta menos o tempo somado de todas as pausas — ver os
    métodos abaixo, exercitados em `tests/test_timer_service.py`.
    """

    materia_id: str
    conteudo_id: Optional[str] = None
    tipo_estudo: TipoEstudo = TipoEstudo.OUTRO
    status: StatusAtividade = StatusAtividade.EM_ANDAMENTO
    iniciado_em: datetime = Field(default_factory=datetime.now)
    finalizado_em: Optional[datetime] = None
    pausas: list[IntervaloPausa] = Field(default_factory=list)
    anotacoes: Optional[str] = None

    def duracao_bruta(self, agora: Optional[datetime] = None) -> timedelta:
        fim = self.finalizado_em or (agora or datetime.now())
        return fim - self.iniciado_em

    def duracao_pausada(self, agora: Optional[datetime] = None) -> timedelta:
        return sum((p.duracao(agora) for p in self.pausas), timedelta())

    def duracao_liquida(self, agora: Optional[datetime] = None) -> timedelta:
        return self.duracao_bruta(agora) - self.duracao_pausada(agora)


# --------------------------------------------------------------------------
# 6. Registro de exercícios
# --------------------------------------------------------------------------


class RegistroExercicio(EntidadeBase):
    """Resultado de uma resolução de exercícios, vinculado a uma
    atividade e a uma matéria (para agregações em `DesempenhoService`).
    """

    atividade_id: str
    materia_id: str
    quantidade: int = Field(ge=0)
    acertos: int = Field(ge=0)

    @field_validator("acertos")
    @classmethod
    def _acertos_nao_pode_exceder_quantidade(cls, v: int, info) -> int:
        quantidade = info.data.get("quantidade")
        if quantidade is not None and v > quantidade:
            raise ValueError("acertos não pode ser maior que a quantidade de questões")
        return v


# --------------------------------------------------------------------------
# 7. Planejamento e ciclo de estudos
# --------------------------------------------------------------------------


class MetaEstudo(EntidadeBase):
    """Uma meta de horas para uma matéria em um período (Planejamento
    de Estudos)."""

    materia_id: str
    periodo: PeriodoPlanejamento = PeriodoPlanejamento.SEMANAL
    horas_meta: float = Field(ge=0)
    inicio: date
    fim: date


class EtapaCiclo(BaseModel):
    """Um passo do Ciclo de Estudos: "estude X por N minutos"."""

    materia_id: str
    duracao_minutos: int = 60
    concluida: bool = False


class CicloEstudos(EntidadeBase):
    """Uma sequência de etapas gerada por
    `services.planning_service.gerar_ciclo_estudos`, que se repete
    indefinidamente."""

    etapas: list[EtapaCiclo] = Field(default_factory=list)
    etapa_atual: int = 0
    ciclos_concluidos: int = 0


# --------------------------------------------------------------------------
# 8. Revisões espaçadas
# --------------------------------------------------------------------------


class Revisao(BaseModel):
    """Uma revisão individual dentro de um `PlanoRevisao`."""

    numero: int
    data_prevista: date
    concluida: bool = False
    data_conclusao: Optional[date] = None


class PlanoRevisao(EntidadeBase):
    """Um plano de repetição espaçada para um conteúdo/atividade
    estudado. `referencia_tipo` é livre ("atividade", "conteudo",
    "materia") para não acoplar o motor de revisão a uma única origem.
    """

    referencia_tipo: str
    referencia_id: str
    materia_id: str
    tipo_agendamento: TipoAgendamentoRevisao
    revisoes: list[Revisao] = Field(default_factory=list)
    anotacao: Optional[str] = None

    # Estado usado apenas quando tipo_agendamento == ADAPTATIVA (algoritmo
    # SM-2): ver services.spaced_repetition_service.calcular_sm2. Nos
    # modos PERIODICA/DIA_DA_SEMANA esses campos ficam nos valores padrão
    # e são ignorados.
    fator_facilidade: float = Field(default=2.5, ge=1.3)
    intervalo_atual_dias: int = Field(default=1, ge=1)
    repeticoes_consecutivas: int = Field(default=0, ge=0)


# --------------------------------------------------------------------------
# 9. Notificações inteligentes
# --------------------------------------------------------------------------


class Notificacao(EntidadeBase):
    """Uma notificação gerada por `services.notification_service`.

    Em produção real isso seria publicado em uma fila (ex.: Celery +
    APScheduler para agendamento, mais um provedor de push/e-mail); aqui
    o `tipo`/`mensagem` já carregam toda a lógica preditiva calculada,
    prontos para qualquer canal de entrega futuro.
    """

    tipo: str
    mensagem: str
    criada_em: datetime = Field(default_factory=datetime.now)
    lida: bool = False
