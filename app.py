"""Início — dashboard do DataStudy.

Ponto de entrada: `streamlit run app.py`. As demais páginas ficam em
`pages/` (convenção de multipage app do Streamlit) e são descobertas
automaticamente pelo menu lateral.
"""

from __future__ import annotations

from datetime import date

import streamlit as st

from datastudy.config import get_repository
from datastudy.domain.models import (
    AtividadeEstudo,
    Conteudo,
    Materia,
    PlanoRevisao,
    RegistroExercicio,
)
from datastudy.services.notification_service import gerar_notificacoes
from datastudy.services.performance_service import DesempenhoService
from datastudy.services.spaced_repetition_service import RevisaoService

st.set_page_config(page_title="DataStudy", page_icon="🧠", layout="wide")


@st.cache_resource
def _repositorios():
    return {
        "materias": get_repository(Materia),
        "conteudos": get_repository(Conteudo),
        "atividades": get_repository(AtividadeEstudo),
        "registros": get_repository(RegistroExercicio),
        "planos": get_repository(PlanoRevisao),
    }


def main() -> None:
    st.title("🧠 DataStudy — seu copiloto de estudos")

    repos = _repositorios()
    revisao_service = RevisaoService(repos["planos"])
    desempenho_service = DesempenhoService(repos["registros"])

    pendentes = revisao_service.pendentes()
    hoje = date.today()
    atrasadas = [par for par in pendentes if par[1].data_prevista < hoje]

    col1, col2, col3 = st.columns(3)
    col1.metric("Revisões para hoje/atrasadas", len(pendentes))
    col2.metric("Matérias cadastradas", len(repos["materias"].listar()))
    col3.metric("Taxa de acerto geral", f"{desempenho_service.taxa_acerto_geral()}%")

    st.subheader("📣 Notificações")
    notificacoes = gerar_notificacoes(
        quantidade_pendentes=len(pendentes) - len(atrasadas),
        quantidade_atrasadas=len(atrasadas),
    )
    if notificacoes:
        for notificacao in notificacoes:
            st.info(notificacao.mensagem)
    else:
        st.caption("Nenhuma notificação no momento. Bons estudos! 📚")

    st.divider()
    st.caption(
        "Use o menu à esquerda para iniciar uma atividade, gerenciar matérias e "
        "edital, revisões, planejamento/ciclo de estudos e desempenho."
    )


if __name__ == "__main__":
    main()
