from datastudy.domain.models import Conteudo, Edital, Materia, TopicoEdital
from datastudy.repositories.json_repository import JsonFileRepository
from datastudy.services.edital_service import EditalService
from datastudy.services.materia_service import MateriaService


def _servicos(tmp_path):
    materias = JsonFileRepository(tmp_path / "materias.json", Materia)
    conteudos = JsonFileRepository(tmp_path / "conteudos.json", Conteudo)
    editais = JsonFileRepository(tmp_path / "editais.json", Edital)
    topicos = JsonFileRepository(tmp_path / "topicos.json", TopicoEdital)
    return (
        MateriaService(materias, conteudos),
        EditalService(editais, topicos, conteudos),
    )


def test_progresso_e_zero_para_edital_sem_topicos(tmp_path):
    _, edital_service = _servicos(tmp_path)
    edital = edital_service.criar_edital("Analista - Tribunal X")
    assert edital_service.progresso(edital.id) == 0.0


def test_progresso_reflete_automaticamente_conteudos_concluidos(tmp_path):
    materia_service, edital_service = _servicos(tmp_path)

    materia = materia_service.criar_materia("Direito Penal")
    c1 = materia_service.adicionar_conteudo(materia.id, "Princípios")
    c2 = materia_service.adicionar_conteudo(materia.id, "Teoria do Crime")
    materia_service.concluir_conteudo(c1.id)  # só o primeiro está concluído

    edital = edital_service.criar_edital("Analista - Tribunal X")
    raiz = edital_service.adicionar_topico(edital.id, "Direito Penal")
    edital_service.adicionar_topico(edital.id, "Princípios", parent_id=raiz.id, conteudo_vinculado_id=c1.id)
    edital_service.adicionar_topico(edital.id, "Teoria do Crime", parent_id=raiz.id, conteudo_vinculado_id=c2.id)

    # sem cadastro manual de percentual: o progresso nasce de conteudo.concluido
    assert abs(edital_service.progresso(edital.id) - 0.5) < 1e-9

    materia_service.concluir_conteudo(c2.id)
    assert edital_service.progresso(edital.id) == 1.0
