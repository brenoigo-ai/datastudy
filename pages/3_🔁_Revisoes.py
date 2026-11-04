"""Requisito 8 na UI: mostra só o que importa agora (revisões de
hoje/atrasadas) — o agendamento futuro já foi resolvido no momento em
que o plano foi criado (`services/spaced_repetition_service.py`)."""

from __future__ import annotations

from datetime import date

import streamlit as st

from datastudy.config import get_repository
from datastudy.domain.enums import TipoAgendamentoRevisao
from datastudy.domain.models import Materia, PlanoRevisao
from datastudy.services.spaced_repetition_service import RevisaoService

st.set_page_config(page_title="Revisões — DataStudy", page_icon="🔁")

#: Rótulos amigáveis para a nota de recall do modo adaptativo (SM-2),
#: que internamente usa uma escala 0-5.
_QUALIDADES_SM2 = {
    "Esqueci (0)": 0,
    "Lembrei errado, mas reconheci a resposta (2)": 2,
    "Acertei com esforço (3)": 3,
    "Acertei bem (4)": 4,
    "Lembrei perfeitamente (5)": 5,
}


@st.cache_resource
def _servicos():
    return {
        "materias_repo": get_repository(Materia),
        "revisao_service": RevisaoService(get_repository(PlanoRevisao)),
    }


servicos = _servicos()
materias = {m.id: m.nome for m in servicos["materias_repo"].listar()}
revisao_service = servicos["revisao_service"]

st.title("🔁 Revisões Espaçadas")

pendentes = revisao_service.pendentes()
hoje = date.today()

if not pendentes:
    st.success("Nenhuma revisão pendente. 🎉")

for plano, revisao in pendentes:
    atrasada = revisao.data_prevista < hoje
    adaptativo = plano.tipo_agendamento == TipoAgendamentoRevisao.ADAPTATIVA

    rotulo = f"{materias.get(plano.materia_id, plano.materia_id)} — Revisão {revisao.numero}"
    rotulo += " 🔴 (atrasada)" if atrasada else " 🟢 (hoje)"
    if adaptativo:
        rotulo += " · adaptativo (SM-2)"
    texto = rotulo + (f" — _{plano.anotacao}_" if plano.anotacao else "")

    if adaptativo:
        # No modo SM-2 não existe "concluir" simples: o próximo intervalo
        # depende da nota de recall que o usuário dá agora mesmo.
        col1, col2, col3 = st.columns([3, 2, 1])
        col1.write(texto)
        qualidade_label = col2.selectbox(
            "Como foi lembrar?",
            list(_QUALIDADES_SM2),
            key=f"qualidade-{plano.id}-{revisao.numero}",
            label_visibility="collapsed",
        )
        if col3.button("✅ Registrar", key=f"concluir-{plano.id}-{revisao.numero}"):
            revisao_service.concluir_revisao_adaptativa(plano.id, _QUALIDADES_SM2[qualidade_label])
            st.rerun()
    else:
        col1, col2, col3 = st.columns([3, 1, 1])
        col1.write(texto)
        if col2.button("✅ Concluir", key=f"concluir-{plano.id}-{revisao.numero}"):
            revisao_service.concluir_revisao(plano.id, revisao.numero)
            st.rerun()
        if col3.button("⏭️ Ignorar", key=f"ignorar-{plano.id}-{revisao.numero}"):
            revisao_service.ignorar(plano.id, escopo="proxima")
            st.rerun()
