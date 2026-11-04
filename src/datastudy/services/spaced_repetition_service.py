"""Requisito 8 — Revisões Espaçadas Automatizadas.

Motor "invisível" no sentido de que, uma vez criado o plano, o usuário
só interage com `pendentes()` (o que precisa revisar hoje/atrasado) —
o agendamento futuro é 100% automático a partir da curva de
esquecimento (intervalos como 1, 7 e 30 dias).

Suporta os dois modos observados no app de referência (Aprovado):
periódica (intervalos de dias livres) e dia-da-semana (um dia fixo,
repetido a cada N semanas).
"""

from __future__ import annotations

from datetime import date, timedelta

from datastudy.domain.enums import TipoAgendamentoRevisao
from datastudy.domain.models import PlanoRevisao, Revisao
from datastudy.repositories.base import Repository

#: Recomendação clássica de repetição espaçada: 1 dia, 1 semana, 1 mês.
INTERVALOS_RECOMENDADOS: tuple[int, ...] = (1, 7, 30)


def calcular_sm2(
    fator_facilidade: float, intervalo_atual_dias: int, repeticoes_consecutivas: int, qualidade: int
) -> tuple[int, float, int]:
    """Algoritmo SM-2 (SuperMemo-2, popularizado pelo Anki).

    Diferença central para o modo `PERIODICA`: ali as datas (1, 7, 30
    dias...) são todas fixadas no dia em que o plano é criado. Aqui, a
    cada revisão o usuário avalia a qualidade da lembrança de 0
    ("esqueci tudo") a 5 ("lembrei perfeitamente"), e o PRÓXIMO
    intervalo só é calculado nesse momento, a partir desse desempenho
    real — se o usuário for mal, o ciclo reinicia; se for bem, o
    intervalo cresce (multiplicado por um "fator de facilidade" que
    também se ajusta a cada rodada). Isso é o que resolve o cronograma
    estático apontado como limitação do modo periódico.

    Retorna `(novo_intervalo_dias, novo_fator_facilidade, novas_repeticoes_consecutivas)`.
    """

    qualidade = max(0, min(5, qualidade))
    novo_fator = max(
        1.3, fator_facilidade + (0.1 - (5 - qualidade) * (0.08 + (5 - qualidade) * 0.02))
    )

    if qualidade < 3:
        # Recall ruim: reinicia a progressão (mas preserva o fator de
        # facilidade acumulado — um tropeço não apaga o histórico todo).
        return 1, novo_fator, 0

    repeticoes = repeticoes_consecutivas + 1
    if repeticoes == 1:
        novo_intervalo = 1
    elif repeticoes == 2:
        novo_intervalo = 6
    else:
        novo_intervalo = round(intervalo_atual_dias * novo_fator)
    return novo_intervalo, novo_fator, repeticoes


class RevisaoService:
    def __init__(self, planos: Repository[PlanoRevisao]) -> None:
        self._planos = planos

    def criar_plano_periodico(
        self,
        materia_id: str,
        referencia_tipo: str,
        referencia_id: str,
        intervalos_dias: list[int] | None = None,
        data_base: date | None = None,
        anotacao: str | None = None,
    ) -> PlanoRevisao:
        intervalos = sorted(intervalos_dias or list(INTERVALOS_RECOMENDADOS))
        data_base = data_base or date.today()
        revisoes = [
            Revisao(numero=i + 1, data_prevista=data_base + timedelta(days=d))
            for i, d in enumerate(intervalos)
        ]
        plano = PlanoRevisao(
            materia_id=materia_id,
            referencia_tipo=referencia_tipo,
            referencia_id=referencia_id,
            tipo_agendamento=TipoAgendamentoRevisao.PERIODICA,
            revisoes=revisoes,
            anotacao=anotacao,
        )
        return self._planos.adicionar(plano)

    def criar_plano_dia_semana(
        self,
        materia_id: str,
        referencia_tipo: str,
        referencia_id: str,
        dia_semana: int,
        quantidade: int,
        intervalo_semanas: int = 1,
        data_base: date | None = None,
        anotacao: str | None = None,
    ) -> PlanoRevisao:
        """`dia_semana` segue a convenção do stdlib (`date.weekday()`):
        0 = segunda-feira ... 6 = domingo."""

        data_base = data_base or date.today()
        dias_ate_o_dia = (dia_semana - data_base.weekday()) % 7
        proxima = data_base + timedelta(days=dias_ate_o_dia or 7)
        revisoes = []
        for i in range(quantidade):
            revisoes.append(Revisao(numero=i + 1, data_prevista=proxima))
            proxima += timedelta(weeks=intervalo_semanas)
        plano = PlanoRevisao(
            materia_id=materia_id,
            referencia_tipo=referencia_tipo,
            referencia_id=referencia_id,
            tipo_agendamento=TipoAgendamentoRevisao.DIA_DA_SEMANA,
            revisoes=revisoes,
            anotacao=anotacao,
        )
        return self._planos.adicionar(plano)

    def criar_plano_adaptativo(
        self,
        materia_id: str,
        referencia_tipo: str,
        referencia_id: str,
        data_base: date | None = None,
        anotacao: str | None = None,
    ) -> PlanoRevisao:
        """Cria um plano no modo SM-2: só a primeira revisão (amanhã) é
        conhecida de antemão; as próximas nascem em `concluir_revisao_adaptativa`,
        uma de cada vez, a partir da qualidade de recall informada."""

        data_base = data_base or date.today()
        primeira = Revisao(numero=1, data_prevista=data_base + timedelta(days=1))
        plano = PlanoRevisao(
            materia_id=materia_id,
            referencia_tipo=referencia_tipo,
            referencia_id=referencia_id,
            tipo_agendamento=TipoAgendamentoRevisao.ADAPTATIVA,
            revisoes=[primeira],
            anotacao=anotacao,
        )
        return self._planos.adicionar(plano)

    def concluir_revisao_adaptativa(self, plano_id: str, qualidade: int) -> PlanoRevisao:
        """Conclui a revisão pendente de um plano ADAPTATIVA e já agenda
        a próxima com base na qualidade informada (0 a 5, estilo SM-2)."""

        plano = self._planos.obter(plano_id)
        if plano is None:
            raise ValueError(f"Plano de revisão {plano_id!r} não encontrado")
        if plano.tipo_agendamento != TipoAgendamentoRevisao.ADAPTATIVA:
            raise ValueError("Este plano não usa o modo adaptativo (SM-2)")

        pendente = next((r for r in plano.revisoes if not r.concluida), None)
        if pendente is None:
            raise ValueError("Não há revisão pendente neste plano")

        pendente.concluida = True
        pendente.data_conclusao = date.today()

        novo_intervalo, novo_fator, novas_repeticoes = calcular_sm2(
            plano.fator_facilidade, plano.intervalo_atual_dias, plano.repeticoes_consecutivas, qualidade
        )
        plano.fator_facilidade = novo_fator
        plano.intervalo_atual_dias = novo_intervalo
        plano.repeticoes_consecutivas = novas_repeticoes
        plano.revisoes.append(
            Revisao(numero=pendente.numero + 1, data_prevista=date.today() + timedelta(days=novo_intervalo))
        )
        return self._planos.atualizar(plano)

    def pendentes(self, hoje: date | None = None) -> list[tuple[PlanoRevisao, Revisao]]:
        """Todas as revisões não concluídas com `data_prevista <= hoje`
        (inclui atrasadas), ordenadas da mais antiga para a mais nova.
        """

        hoje = hoje or date.today()
        resultado = [
            (plano, revisao)
            for plano in self._planos.listar()
            for revisao in plano.revisoes
            if not revisao.concluida and revisao.data_prevista <= hoje
        ]
        return sorted(resultado, key=lambda par: par[1].data_prevista)

    def concluir_revisao(self, plano_id: str, numero: int) -> PlanoRevisao:
        plano = self._planos.obter(plano_id)
        if plano is None:
            raise ValueError(f"Plano de revisão {plano_id!r} não encontrado")
        for revisao in plano.revisoes:
            if revisao.numero == numero:
                revisao.concluida = True
                revisao.data_conclusao = date.today()
                break
        else:
            raise ValueError(f"Revisão {numero} não encontrada no plano {plano_id!r}")
        return self._planos.atualizar(plano)

    def ignorar(self, plano_id: str, escopo: str = "proxima") -> PlanoRevisao:
        """`escopo`: "proxima" | "atrasadas" | "todas" — espelha as três
        opções de "Qual revisão você deseja ignorar?" do app de
        referência."""

        plano = self._planos.obter(plano_id)
        if plano is None:
            raise ValueError(f"Plano de revisão {plano_id!r} não encontrado")
        hoje = date.today()
        pendentes = [r for r in plano.revisoes if not r.concluida]
        if escopo == "proxima" and pendentes:
            alvo = [min(pendentes, key=lambda r: r.data_prevista)]
        elif escopo == "atrasadas":
            alvo = [r for r in pendentes if r.data_prevista < hoje]
        else:
            alvo = pendentes
        for revisao in alvo:
            revisao.concluida = True
            revisao.data_conclusao = hoje
        return self._planos.atualizar(plano)
