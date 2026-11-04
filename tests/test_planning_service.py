from datastudy.domain.enums import Dificuldade
from datastudy.domain.models import Materia
from datastudy.services.planning_service import (
    RoundRobinPonderadoSuave,
    gerar_ciclo_estudos,
    gerar_planejamento,
    peso_efetivo,
)


def _materia(nome, dificuldade=Dificuldade.MEDIA, peso=1.0, questoes=None):
    return Materia(nome=nome, dificuldade=dificuldade, peso=peso, qtd_questoes_prova=questoes)


def test_materia_mais_dificil_recebe_peso_maior():
    facil = _materia("Fácil", Dificuldade.FACIL)
    dificil = _materia("Difícil", Dificuldade.DIFICIL)
    assert peso_efetivo(dificil, 0) > peso_efetivo(facil, 0)


def test_materia_com_mais_questoes_recebe_peso_maior():
    poucas = _materia("Poucas questões", questoes=5)
    muitas = _materia("Muitas questões", questoes=25)
    assert peso_efetivo(muitas, 30) > peso_efetivo(poucas, 30)


def test_planejamento_distribui_todas_as_horas_disponiveis():
    materias = [_materia("A"), _materia("B"), _materia("C")]
    metas = gerar_planejamento(materias, horas_disponiveis=10)
    assert abs(sum(m.horas_meta for m in metas) - 10) < 0.05


def test_planejamento_vazio_sem_materias():
    assert gerar_planejamento([], horas_disponiveis=10) == []


def test_ciclo_estudos_gera_a_quantidade_pedida_de_etapas():
    materias = [_materia("A"), _materia("B")]
    ciclo = gerar_ciclo_estudos(materias, tamanho_ciclo=10)
    assert len(ciclo.etapas) == 10


def test_round_robin_respeita_proporcao_de_pesos_no_longo_prazo():
    pesos = {"A": 3.0, "B": 1.0}  # A deveria aparecer ~75% das vezes
    swrr = RoundRobinPonderadoSuave(pesos)
    escolhas = [swrr.proximo() for _ in range(400)]
    proporcao_a = escolhas.count("A") / len(escolhas)
    assert 0.65 < proporcao_a < 0.85


def test_round_robin_intercala_sem_longas_repeticoes_quando_pesos_sao_iguais():
    pesos = {"A": 1.0, "B": 1.0, "C": 1.0}
    swrr = RoundRobinPonderadoSuave(pesos)
    escolhas = [swrr.proximo() for _ in range(30)]
    maior_sequencia = atual = 1
    for anterior, item in zip(escolhas, escolhas[1:]):
        atual = atual + 1 if anterior == item else 1
        maior_sequencia = max(maior_sequencia, atual)
    assert maior_sequencia <= 2
