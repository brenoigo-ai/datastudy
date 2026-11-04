"""Requisito 7 na UI: dois modos (planejamento por horas / ciclo),
ambos alimentados pelo mesmo núcleo de ponderação em
`services/planning_service.py`."""

from __future__ import annotations

import streamlit as st

from datastudy.config import get_repository
from datastudy.domain.enums import PeriodoPlanejamento
from datastudy.domain.models import CicloEstudos, Materia, MetaEstudo
from datastudy.services.planning_service import gerar_ciclo_estudos, gerar_planejamento

st.set_page_config(page_title="Planejamento e Ciclo — DataStudy", page_icon="🎯")


@st.cache_resource
def _servicos():
    return {
        "materias_repo": get_repository(Materia),
        "metas_repo": get_repository(MetaEstudo),
        "ciclos_repo": get_repository(CicloEstudos),
    }


servicos = _servicos()
materias = servicos["materias_repo"].listar()

st.title("🎯 Planejamento e Ciclo de Estudos")

if not materias:
    st.warning("Cadastre matérias na página **Matérias e Edital** antes de gerar um planejamento.")
    st.stop()

modo = st.radio("Modo", ["Planejamento por horas (semanal/mensal)", "Ciclo de estudos"], horizontal=True)
nomes = {m.id: m.nome for m in materias}

if modo.startswith("Planejamento"):
    horas = st.number_input("Horas disponíveis no período", min_value=1.0, value=10.0, step=0.5)
    periodo = st.selectbox("Período", list(PeriodoPlanejamento), format_func=lambda p: p.value.title())
    if st.button("Gerar planejamento", type="primary"):
        metas = gerar_planejamento(materias, horas, periodo)
        for meta in metas:
            servicos["metas_repo"].adicionar(meta)
        st.session_state["ultimo_planejamento"] = metas

    for meta in st.session_state.get("ultimo_planejamento", []):
        st.progress(0.0, text=f"{nomes.get(meta.materia_id, meta.materia_id)} — meta de {meta.horas_meta}h")

else:
    duracao_etapa = st.slider("Duração de cada etapa (minutos)", 15, 120, 60, step=15)
    tamanho = st.slider("Número de etapas no ciclo", len(materias), len(materias) * 6, len(materias) * 3)
    if st.button("Gerar ciclo", type="primary"):
        ciclo = gerar_ciclo_estudos(materias, duracao_etapa, tamanho)
        servicos["ciclos_repo"].adicionar(ciclo)
        st.session_state["ultimo_ciclo"] = ciclo

    ciclo = st.session_state.get("ultimo_ciclo")
    if ciclo:
        st.write("**Sequência gerada** (matérias mais difíceis/pesadas aparecem mais vezes, intercaladas):")
        sequencia = " → ".join(f"{nomes.get(e.materia_id, '?')} ({e.duracao_minutos}min)" for e in ciclo.etapas)
        st.markdown(sequencia)
