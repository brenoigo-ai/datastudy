"""Requisitos 1 e 2: CRUD de Matérias/Conteúdos + Edital Verticalizado
com progresso automático (a barra de progresso nunca é digitada à
mão — nasce de `EditalService.progresso`)."""

from __future__ import annotations

import streamlit as st

from datastudy.config import get_repository
from datastudy.domain.enums import Dificuldade
from datastudy.domain.models import Conteudo, Edital, Materia, TopicoEdital
from datastudy.services.edital_service import EditalService
from datastudy.services.materia_service import MateriaService

st.set_page_config(page_title="Matérias e Edital — DataStudy", page_icon="📚")


@st.cache_resource
def _servicos():
    materias_repo = get_repository(Materia)
    conteudos_repo = get_repository(Conteudo)
    return {
        "materia_service": MateriaService(materias_repo, conteudos_repo),
        "edital_service": EditalService(get_repository(Edital), get_repository(TopicoEdital), conteudos_repo),
    }


servicos = _servicos()
materia_service = servicos["materia_service"]
edital_service = servicos["edital_service"]

st.title("📚 Matérias, Conteúdos e Edital")

aba_materias, aba_edital = st.tabs(["Matérias e Conteúdos", "Edital Verticalizado"])

with aba_materias:
    with st.form("nova_materia", clear_on_submit=True):
        st.write("**Nova matéria**")
        nome = st.text_input("Nome da matéria")
        col1, col2, col3 = st.columns(3)
        dificuldade = col1.selectbox("Dificuldade", list(Dificuldade), format_func=lambda d: d.value.title())
        peso = col2.number_input("Peso", min_value=0.1, value=1.0, step=0.1)
        questoes = col3.number_input("Questões na prova", min_value=0, value=0, step=1)
        if st.form_submit_button("Adicionar matéria") and nome:
            materia_service.criar_materia(
                nome, dificuldade=dificuldade, peso=peso, qtd_questoes_prova=questoes or None
            )
            st.rerun()

    for materia in materia_service.listar_materias():
        with st.expander(f"{materia.nome} — dificuldade {materia.dificuldade.value}, peso {materia.peso}"):
            for conteudo in materia_service.listar_conteudos(materia.id):
                marcado = st.checkbox(conteudo.nome, value=conteudo.concluido, key=f"conteudo-{conteudo.id}")
                if marcado != conteudo.concluido:
                    materia_service.concluir_conteudo(conteudo.id, concluido=marcado)
                    st.rerun()

            novo_conteudo = st.text_input("Novo conteúdo", key=f"novo-conteudo-{materia.id}")
            col_add, col_del = st.columns(2)
            if col_add.button("➕ Adicionar conteúdo", key=f"btn-conteudo-{materia.id}") and novo_conteudo:
                materia_service.adicionar_conteudo(materia.id, novo_conteudo)
                st.rerun()
            if col_del.button("🗑️ Remover matéria", key=f"remover-{materia.id}"):
                materia_service.remover_materia(materia.id)
                st.rerun()

with aba_edital:
    with st.form("novo_edital", clear_on_submit=True):
        st.write("**Novo edital**")
        nome_edital = st.text_input("Cargo / concurso")
        orgao = st.text_input("Órgão (opcional)")
        if st.form_submit_button("Criar edital") and nome_edital:
            edital_service.criar_edital(nome_edital, orgao or None)
            st.rerun()

    for edital in edital_service.listar_editais():
        progresso = edital_service.progresso(edital.id)
        st.progress(progresso, text=f"{edital.nome} — {progresso * 100:.1f}% concluído (automático)")

        with st.expander(f"Tópicos de {edital.nome}"):
            for topico in edital_service.listar_topicos(edital.id):
                sub_progresso = edital_service.progresso(edital.id, parent_id=topico.id)
                st.write(f"**{topico.nome}** — {sub_progresso * 100:.0f}%")

            col1, col2 = st.columns(2)
            novo_topico = col1.text_input("Novo tópico raiz", key=f"topico-{edital.id}")
            if col1.button("Adicionar tópico", key=f"btn-topico-{edital.id}") and novo_topico:
                edital_service.adicionar_topico(edital.id, novo_topico)
                st.rerun()

            conteudos_disponiveis = [
                c for m in materia_service.listar_materias() for c in materia_service.listar_conteudos(m.id)
            ]
            topicos_raiz = edital_service.listar_topicos(edital.id)
            if topicos_raiz and conteudos_disponiveis:
                topico_pai = col2.selectbox(
                    "Vincular conteúdo a", topicos_raiz, format_func=lambda t: t.nome, key=f"pai-{edital.id}"
                )
                conteudo_vinculo = col2.selectbox(
                    "Conteúdo", conteudos_disponiveis, format_func=lambda c: c.nome, key=f"vinculo-{edital.id}"
                )
                if col2.button("Vincular como subtópico", key=f"btn-vinculo-{edital.id}"):
                    edital_service.adicionar_topico(
                        edital.id, conteudo_vinculo.nome, parent_id=topico_pai.id,
                        conteudo_vinculado_id=conteudo_vinculo.id,
                    )
                    st.rerun()
