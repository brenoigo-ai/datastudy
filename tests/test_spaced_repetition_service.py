from datetime import date, timedelta

from datastudy.domain.models import PlanoRevisao
from datastudy.repositories.json_repository import JsonFileRepository
from datastudy.services.spaced_repetition_service import RevisaoService, calcular_sm2


def _servico(tmp_path):
    repo = JsonFileRepository(tmp_path / "planos.json", PlanoRevisao)
    return RevisaoService(repo)


def test_plano_periodico_gera_datas_nos_intervalos_corretos(tmp_path):
    servico = _servico(tmp_path)
    base = date(2026, 1, 1)
    plano = servico.criar_plano_periodico(
        "materia-1", "conteudo", "conteudo-1", intervalos_dias=[1, 7, 30], data_base=base
    )
    datas = [r.data_prevista for r in plano.revisoes]
    assert datas == [base + timedelta(days=1), base + timedelta(days=7), base + timedelta(days=30)]


def test_pendentes_considera_apenas_nao_concluidas_e_ja_vencidas(tmp_path):
    servico = _servico(tmp_path)
    base = date(2026, 1, 1)
    servico.criar_plano_periodico("materia-1", "conteudo", "conteudo-1", intervalos_dias=[1, 10], data_base=base)
    pendentes = servico.pendentes(hoje=base + timedelta(days=2))
    assert len(pendentes) == 1
    assert pendentes[0][1].numero == 1


def test_concluir_revisao_marca_como_feita(tmp_path):
    servico = _servico(tmp_path)
    plano = servico.criar_plano_periodico("materia-1", "conteudo", "conteudo-1", intervalos_dias=[1])
    atualizado = servico.concluir_revisao(plano.id, numero=1)
    assert atualizado.revisoes[0].concluida is True
    assert atualizado.revisoes[0].data_conclusao == date.today()


def test_ignorar_apenas_a_proxima(tmp_path):
    servico = _servico(tmp_path)
    base = date(2026, 1, 1)
    plano = servico.criar_plano_periodico(
        "materia-1", "conteudo", "conteudo-1", intervalos_dias=[1, 7, 30], data_base=base
    )
    atualizado = servico.ignorar(plano.id, escopo="proxima")
    concluidas = [r.numero for r in atualizado.revisoes if r.concluida]
    assert concluidas == [1]


def test_sm2_aumenta_intervalo_progressivamente_quando_recall_e_bom():
    intervalo1, fator1, rep1 = calcular_sm2(2.5, 1, 0, qualidade=5)
    assert (intervalo1, rep1) == (1, 1)
    intervalo2, fator2, rep2 = calcular_sm2(fator1, intervalo1, rep1, qualidade=5)
    assert (intervalo2, rep2) == (6, 2)
    intervalo3, _, rep3 = calcular_sm2(fator2, intervalo2, rep2, qualidade=5)
    assert intervalo3 > intervalo2  # a partir da 3ª repetição, cresce por fator_facilidade
    assert rep3 == 3


def test_sm2_reinicia_a_progressao_quando_o_recall_e_ruim():
    intervalo, _, repeticoes = calcular_sm2(2.5, 30, 4, qualidade=1)
    assert intervalo == 1
    assert repeticoes == 0


def test_sm2_fator_de_facilidade_tem_piso_de_1_3():
    _, fator, _ = calcular_sm2(1.3, 1, 0, qualidade=0)
    assert fator >= 1.3


def test_plano_adaptativo_agenda_a_proxima_revisao_so_apos_concluir_a_atual(tmp_path):
    servico = _servico(tmp_path)
    base = date(2026, 1, 1)
    plano = servico.criar_plano_adaptativo("materia-1", "conteudo", "conteudo-1", data_base=base)
    assert len(plano.revisoes) == 1
    assert plano.revisoes[0].data_prevista == base + timedelta(days=1)

    atualizado = servico.concluir_revisao_adaptativa(plano.id, qualidade=5)
    assert len(atualizado.revisoes) == 2  # a próxima só nasce agora, com a data calculada na hora
    assert atualizado.revisoes[0].concluida is True
    assert atualizado.revisoes[1].data_prevista == date.today() + timedelta(days=1)
    assert atualizado.repeticoes_consecutivas == 1


def test_plano_dia_da_semana_gera_a_quantidade_pedida(tmp_path):
    servico = _servico(tmp_path)
    plano = servico.criar_plano_dia_semana(
        "materia-1", "materia", "materia-1", dia_semana=5, quantidade=4, intervalo_semanas=2,
        data_base=date(2026, 1, 1),  # quinta-feira
    )
    assert len(plano.revisoes) == 4
    # cada revisão deve cair exatamente no dia da semana pedido (5 = sábado)
    assert all(r.data_prevista.weekday() == 5 for r in plano.revisoes)
