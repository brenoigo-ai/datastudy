"""Requisitos 5 e 6 na UI: gráficos de taxa de acerto por matéria e de
distribuição de tempo por tipo de estudo."""

from __future__ import annotations

import plotly.express as px
import streamlit as st

from datastudy.config import get_repository
from datastudy.domain.models import AtividadeEstudo, Materia, RegistroExercicio
from datastudy.services.performance_service import DesempenhoService, linha_do_tempo, tempo_por_tipo_estudo

st.set_page_config(page_title="Desempenho — DataStudy", page_icon="📊")


@st.cache_resource
def _servicos():
    return {
        "materias_repo": get_repository(Materia),
        "registros_repo": get_repository(RegistroExercicio),
        "atividades_repo": get_repository(AtividadeEstudo),
    }


servicos = _servicos()
materias = {m.id: m.nome for m in servicos["materias_repo"].listar()}
desempenho = DesempenhoService(servicos["registros_repo"])

st.title("📊 Desempenho e Tempo de Estudo")

col1, col2 = st.columns(2)
totais = desempenho.totais()
col1.metric("Questões resolvidas", totais["questoes"])
col2.metric("Taxa de acerto geral", f"{desempenho.taxa_acerto_geral()}%")

taxa_por_materia = desempenho.taxa_acerto_por_materia()
if taxa_por_materia:
    fig = px.bar(
        x=[materias.get(mid, mid) for mid in taxa_por_materia],
        y=list(taxa_por_materia.values()),
        labels={"x": "Matéria", "y": "Taxa de acerto (%)"},
        title="Taxa de acerto por matéria",
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.caption("Registre exercícios na página **Nova Atividade** para ver seu desempenho por matéria.")

atividades = servicos["atividades_repo"].listar()
if atividades:
    contagem_tipo = tempo_por_tipo_estudo(atividades)
    fig2 = px.pie(
        names=list(contagem_tipo.keys()), values=list(contagem_tipo.values()),
        title="Distribuição por tipo de estudo",
    )
    st.plotly_chart(fig2, use_container_width=True)
else:
    st.caption("Conclua atividades para ver a distribuição por tipo de estudo.")

st.divider()
st.subheader("📈 Linha do Tempo")
dados_linha = linha_do_tempo(atividades)
if dados_linha:
    fig_linha = px.bar(
        x=[dia.isoformat() for dia in dados_linha.keys()],
        y=list(dados_linha.values()),
        labels={"x": "Data", "y": "Horas líquidas"},
        title="Horas estudadas por dia",
    )
    fig_linha.update_xaxes(type="category")
    st.plotly_chart(fig_linha, use_container_width=True)
else:
    st.caption("Conclua atividades para visualizar seu histórico de horas por dia.")
