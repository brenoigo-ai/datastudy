"""Requisitos 3, 4, 6 e 8 reunidos no fluxo de uma atividade: cronômetro
com pausa ativa -> ao concluir, registrar exercícios e/ou agendar
revisão espaçada — o mesmo fluxo do app de referência ("assim que você
encerrar uma atividade de estudo, ali na mesma tela você poderá criar
um plano de revisões")."""

from __future__ import annotations

import streamlit as st

from datastudy.config import get_repository
from datastudy.domain.enums import TipoEstudo
from datastudy.domain.models import AtividadeEstudo, Conteudo, Materia, PlanoRevisao, RegistroExercicio
from datastudy.services.materia_service import MateriaService
from datastudy.services.spaced_repetition_service import INTERVALOS_RECOMENDADOS, RevisaoService
from datastudy.services.timer_service import TimerService
from datastudy.utils.datetime_utils import formatar_duracao

st.set_page_config(page_title="Nova Atividade — DataStudy", page_icon="⏱️")


@st.cache_resource
def _servicos():
    atividades_repo = get_repository(AtividadeEstudo)
    return {
        "materia_service": MateriaService(get_repository(Materia), get_repository(Conteudo)),
        "timer_service": TimerService(atividades_repo),
        "revisao_service": RevisaoService(get_repository(PlanoRevisao)),
        "registros_repo": get_repository(RegistroExercicio),
        "atividades_repo": atividades_repo,
    }


servicos = _servicos()
materia_service = servicos["materia_service"]
timer_service = servicos["timer_service"]

st.title("⏱️ Nova Atividade de Estudo")

materias = materia_service.listar_materias()
if not materias:
    st.warning("Cadastre uma matéria na página **Matérias e Edital** antes de iniciar uma atividade.")
    st.stop()

st.session_state.setdefault("atividade_atual_id", None)
st.session_state.setdefault("sugestao_descanso", None)

atividade_atual = (
    servicos["atividades_repo"].obter(st.session_state.atividade_atual_id)
    if st.session_state.atividade_atual_id
    else None
)

if atividade_atual is None:
    materia = st.selectbox("Matéria", materias, format_func=lambda m: m.nome)
    conteudos = materia_service.listar_conteudos(materia.id)
    conteudo = st.selectbox(
        "Conteúdo (opcional)", [None, *conteudos], format_func=lambda c: "—" if c is None else c.nome
    )
    tipo = st.selectbox(
        "Tipo de estudo", list(TipoEstudo), format_func=lambda t: t.value.replace("_", " ").title()
    )
    meta_tempo_minutos = st.number_input("Meta de tempo (minutos, 0 = sem meta)", min_value=0, value=0, step=5)
    if st.button("▶️ Iniciar", type="primary"):
        nova = timer_service.iniciar(materia.id, conteudo.id if conteudo else None, tipo)
        st.session_state.atividade_atual_id = nova.id
        st.session_state.meta_tempo_minutos = meta_tempo_minutos
        st.rerun()

else:
    # Busca defensiva: se a matéria foi excluída enquanto a atividade
    # seguia em andamento, `atividade_atual.materia_id` fica "órfão" —
    # sem isso, a página quebraria com StopIteration.
    materia = next((m for m in materias if m.id == atividade_atual.materia_id), None)
    if materia is None:
        st.error(
            "A matéria desta atividade não existe mais (foi excluída). "
            "Conclua a atividade para poder iniciar uma nova."
        )
        if st.button("Concluir mesmo assim"):
            timer_service.concluir(atividade_atual.id)
            st.session_state.atividade_atual_id = None
            st.rerun()
        st.stop()

    st.subheader(f"Estudando: {materia.nome}")

    if atividade_atual.status.value == "em_andamento":
        duracao_atual = atividade_atual.duracao_liquida()
        st.metric("Tempo líquido até agora", formatar_duracao(duracao_atual))

        meta_minutos = st.session_state.get("meta_tempo_minutos", 0)
        if meta_minutos:
            progresso = min(duracao_atual.total_seconds() / (meta_minutos * 60), 1.0)
            texto_meta = f"Meta: {meta_minutos} min ({int(progresso * 100)}%)"
            if progresso >= 1.0:
                st.success(f"🎯 Meta de {meta_minutos} min atingida!")
            st.progress(progresso, text=texto_meta)

        col1, col2 = st.columns(2)
        if col1.button("⏸️ Pausar"):
            _, sugestao = timer_service.pausar(atividade_atual.id)
            st.session_state.sugestao_descanso = sugestao
            st.rerun()
        if col2.button("✅ Concluir"):
            timer_service.concluir(atividade_atual.id)
            st.session_state["atividade_finalizada_id"] = atividade_atual.id
            st.session_state.atividade_atual_id = None
            st.rerun()

    elif atividade_atual.status.value == "pausada":
        st.warning("⏸️ Pausado — aproveite para descansar ativamente:")
        sugestao = st.session_state.sugestao_descanso
        if sugestao:
            st.markdown(f"**🫁 Respiração:** {sugestao.respiracao}")
            st.markdown(f"**🤸 Alongamento:** {sugestao.alongamento}")
            st.caption(f"Sugestão de ~{sugestao.duracao_sugerida_segundos}s de descanso.")
        if st.button("▶️ Retomar"):
            timer_service.retomar(atividade_atual.id)
            st.rerun()

if st.session_state.get("atividade_finalizada_id"):
    st.success("Atividade concluída! Registre seu desempenho e, se quiser, agende revisões.")
    atividade = servicos["atividades_repo"].obter(st.session_state["atividade_finalizada_id"])

    with st.form("registro_pos_atividade"):
        st.write("**Registro de exercícios (opcional)**")
        col1, col2 = st.columns(2)
        quantidade = col1.number_input("Quantidade de questões", min_value=0, value=0)
        acertos = col2.number_input("Acertos", min_value=0, value=0)

        st.write("**Agendar revisão espaçada (opcional)**")
        modo_revisao = st.radio(
            "Modo de revisão",
            [
                "Nenhuma",
                f"Fixo ({', '.join(str(d) for d in INTERVALOS_RECOMENDADOS)} dias)",
                "Adaptativo (SM-2 — ajusta o intervalo pela sua nota a cada revisão)",
            ],
        )
        anotacao = st.text_input("Anotação para o seu 'eu do futuro'", placeholder="Ex.: revisar até a página 30")

        if st.form_submit_button("Salvar") and atividade is not None:
            if quantidade > 0:
                servicos["registros_repo"].adicionar(
                    RegistroExercicio(
                        atividade_id=atividade.id,
                        materia_id=atividade.materia_id,
                        quantidade=int(quantidade),
                        acertos=int(min(acertos, quantidade)),
                    )
                )
            if modo_revisao.startswith("Fixo"):
                servicos["revisao_service"].criar_plano_periodico(
                    materia_id=atividade.materia_id,
                    referencia_tipo="atividade",
                    referencia_id=atividade.id,
                    intervalos_dias=list(INTERVALOS_RECOMENDADOS),
                    anotacao=anotacao or None,
                )
            elif modo_revisao.startswith("Adaptativo"):
                servicos["revisao_service"].criar_plano_adaptativo(
                    materia_id=atividade.materia_id,
                    referencia_tipo="atividade",
                    referencia_id=atividade.id,
                    anotacao=anotacao or None,
                )
            del st.session_state["atividade_finalizada_id"]
            st.success("Salvo!")
            st.rerun()
