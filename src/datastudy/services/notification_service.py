"""Requisito 9 — Notificações Inteligentes.

"Preditivo" aqui é literal, não só cosmético: `notificacao_ritmo_semanal`
projeta linearmente o ritmo atual (horas feitas / dias já passados na
semana) para estimar se a meta será cumprida — a mesma lógica que
qualquer app sério de metas usa, só que transparente e testável.

Em produção real, isso alimentaria um agendador (ex.: APScheduler) que
dispara push/e-mail; aqui o foco é a lógica que decide *o quê* dizer.
"""

from __future__ import annotations

from datastudy.domain.models import Notificacao


def notificacao_ritmo_semanal(
    horas_feitas: float, horas_meta: float, dias_passados_na_semana: int
) -> Notificacao | None:
    if dias_passados_na_semana <= 0 or horas_meta <= 0:
        return None
    ritmo_diario = horas_feitas / dias_passados_na_semana
    projecao = round(ritmo_diario * 7, 1)
    if projecao >= horas_meta:
        mensagem = (
            f"No ritmo atual você deve fechar a semana com ~{projecao}h, "
            f"superando sua meta de {horas_meta}h. 🚀"
        )
    else:
        faltam = round(horas_meta - projecao, 1)
        mensagem = (
            f"No ritmo atual você fecharia a semana com ~{projecao}h, "
            f"{faltam}h abaixo da meta de {horas_meta}h. Ajuste o passo! ⚠️"
        )
    return Notificacao(tipo="ritmo_semanal", mensagem=mensagem)


def notificacao_revisoes_do_dia(
    quantidade_pendentes: int, quantidade_atrasadas: int
) -> Notificacao | None:
    if quantidade_pendentes == 0 and quantidade_atrasadas == 0:
        return None
    partes = []
    if quantidade_pendentes:
        partes.append(f"{quantidade_pendentes} revisão(ões) para hoje")
    if quantidade_atrasadas:
        partes.append(f"{quantidade_atrasadas} atrasada(s)")
    return Notificacao(
        tipo="revisoes", mensagem="Você tem " + " e ".join(partes) + ". Bora recuperar o terreno! 📚"
    )


def notificacao_sequencia(dias_consecutivos: int) -> Notificacao | None:
    if dias_consecutivos < 2:
        return None
    return Notificacao(
        tipo="sequencia",
        mensagem=f"Sequência de {dias_consecutivos} dias estudando. Não quebre a corrente! 🔥",
    )


def gerar_notificacoes(
    *,
    quantidade_pendentes: int = 0,
    quantidade_atrasadas: int = 0,
    horas_feitas: float | None = None,
    horas_meta: float | None = None,
    dias_passados_na_semana: int | None = None,
    dias_consecutivos: int | None = None,
) -> list[Notificacao]:
    """Agrega todas as notificações aplicáveis ao estado atual do
    usuário. Cada parâmetro é opcional — a página que chamar decide
    quais sinais tem disponíveis no momento."""

    notificacoes = []
    n = notificacao_revisoes_do_dia(quantidade_pendentes, quantidade_atrasadas)
    if n:
        notificacoes.append(n)
    if horas_feitas is not None and horas_meta is not None and dias_passados_na_semana is not None:
        n = notificacao_ritmo_semanal(horas_feitas, horas_meta, dias_passados_na_semana)
        if n:
            notificacoes.append(n)
    if dias_consecutivos is not None:
        n = notificacao_sequencia(dias_consecutivos)
        if n:
            notificacoes.append(n)
    return notificacoes
