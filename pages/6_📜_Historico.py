"""Histórico: ver, corrigir e excluir atividades passadas.

Gap real de paridade com o app de referência (Aprovado tem "Histórico"
como item de menu próprio) que a primeira entrega desta arquitetura
tinha deixado de fora — adicionada nesta rodada de revisão.
"""

from __future__ import annotations

from datetime import timedelta

import streamlit as st

from datastudy.config import get_repository
from datastudy.domain.enums import StatusAtividade
from datastudy.domain.models import AtividadeEstudo, Materia
from datastudy.utils.datetime_utils import formatar_duracao

st.set_page_config(page_title="Histórico — DataStudy", page_icon="📜")


@st.cache_resource
def _servicos():
    return {
        "atividades_repo": get_repository(AtividadeEstudo),
        "materias_repo": get_repository(Materia),
    }


servicos = _servicos()
atividades_repo = servicos["atividades_repo"]
materias_dict = {m.id: m.nome for m in servicos["materias_repo"].listar()}

st.title("📜 Histórico de Atividades")

atividades = sorted(atividades_repo.listar(), key=lambda a: a.iniciado_em, reverse=True)

if not atividades:
    st.info("Nenhuma atividade registrada no histórico.")
    st.stop()

for atividade in atividades:
    materia_nome = materias_dict.get(atividade.materia_id, "Matéria excluída")
    data_str = atividade.iniciado_em.strftime("%d/%m/%Y")
    duracao_str = formatar_duracao(atividade.duracao_liquida())
    status_str = "✅ Concluída" if atividade.status == StatusAtividade.CONCLUIDA else "⚠️ Em andamento/Pausada"

    with st.expander(f"{data_str} · {materia_nome} · {duracao_str} · {status_str}"):
        st.write(f"**Tipo:** {atividade.tipo_estudo.value.replace('_', ' ').title()}")
        st.write(f"**Início:** {atividade.iniciado_em.strftime('%H:%M:%S')}")
        if atividade.finalizado_em:
            st.write(f"**Fim:** {atividade.finalizado_em.strftime('%H:%M:%S')}")

        col1, col2 = st.columns(2)

        if col1.button("🗑️ Excluir atividade", key=f"del_{atividade.id}"):
            atividades_repo.remover(atividade.id)
            st.success("Atividade removida!")
            st.rerun()

        nova_duracao = col2.number_input(
            "Ajustar tempo líquido (minutos)",
            min_value=0,
            value=int(atividade.duracao_liquida().total_seconds() // 60),
            key=f"edit_{atividade.id}",
        )

        if col2.button("💾 Guardar ajuste", key=f"save_{atividade.id}"):
            # Zera as pausas e recalcula o fim a partir do início: como
            # duração líquida = bruta - pausas, isso força
            # duracao_liquida() a bater exatamente com o valor ajustado.
            # Usamos StatusAtividade.CONCLUIDA (o enum), não a string
            # "concluida" solta — atribuir a string crua deixaria o
            # objeto em memória sem o método .value até a próxima
            # releitura do repositório (pydantic não valida atribuição
            # direta por padrão), o que quebraria qualquer código nesta
            # mesma execução que chamasse `.status.value` em seguida.
            atividade.pausas = []
            atividade.finalizado_em = atividade.iniciado_em + timedelta(minutes=int(nova_duracao))
            atividade.status = StatusAtividade.CONCLUIDA
            atividades_repo.atualizar(atividade)
            st.success("Tempo ajustado!")
            st.rerun()
