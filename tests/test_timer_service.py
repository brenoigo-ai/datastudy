import time

from datastudy.domain.enums import StatusAtividade, TipoEstudo
from datastudy.domain.models import AtividadeEstudo
from datastudy.repositories.json_repository import JsonFileRepository
from datastudy.services.timer_service import TimerService, sugerir_descanso


def test_duracao_liquida_desconta_o_tempo_pausado(tmp_path):
    repo = JsonFileRepository(tmp_path / "atividades.json", AtividadeEstudo)
    servico = TimerService(repo)

    atividade = servico.iniciar("materia-1", None, TipoEstudo.LEITURA)
    time.sleep(0.2)
    atividade, sugestao = servico.pausar(atividade.id)
    assert atividade.status == StatusAtividade.PAUSADA
    assert sugestao.respiracao and sugestao.alongamento

    time.sleep(0.2)  # tempo de pausa que NÃO deve contar como estudo
    servico.retomar(atividade.id)
    time.sleep(0.2)
    concluida = servico.concluir(atividade.id)

    liquida = concluida.duracao_liquida().total_seconds()
    bruta = concluida.duracao_bruta().total_seconds()
    assert 0 < liquida < bruta


def test_pausar_atividade_que_nao_esta_em_andamento_falha(tmp_path):
    repo = JsonFileRepository(tmp_path / "atividades.json", AtividadeEstudo)
    servico = TimerService(repo)
    atividade = servico.iniciar("materia-1", None, TipoEstudo.LEITURA)
    servico.pausar(atividade.id)
    try:
        servico.pausar(atividade.id)  # já está pausada
        assert False, "deveria ter levantado ValueError"
    except ValueError:
        pass


def test_sugestao_de_descanso_varia_por_numero_de_pausa():
    primeira = sugerir_descanso(0)
    segunda = sugerir_descanso(1)
    assert primeira != segunda
