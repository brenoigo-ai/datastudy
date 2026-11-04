import csv
import io
import streamlit as st
from datastudy.services.ai_flashcards import (
    ErroValidacaoIA,
    gerar_flashcards_gemini,
    obter_chave_gemini,
)

st.set_page_config(page_title="Flashcards IA | DataStudy", page_icon="🤖", layout="wide")

st.title("🤖 Gerador de Flashcards com IA")
st.caption("Extraia perguntas e respostas das suas apostilas e exporte direto para o Anki (CSV).")

chave_configurada = bool(obter_chave_gemini())
if not chave_configurada:
    st.info(
        "💡 Configure a variável de ambiente GEMINI_API_KEY (ou st.secrets na nuvem) "
        "para gerar flashcards automaticamente com o Google Gemini."
    )

with st.form("form_flashcards_ia"):
    resumo = st.text_area(
        "Cole o resumo da aula, artigo ou apostila:",
        height=180,
        placeholder="Ex: A Primeira Forma Normal (1FN) exige que todos os atributos de uma tabela contenham apenas valores atômicos...",
    )
    quantidade = st.slider("Quantidade de flashcards", min_value=1, max_value=15, value=5)
    submetido = st.form_submit_button("✨ Gerar Flashcards", use_container_width=True)

if submetido:
    try:
        with st.spinner("Analisando conteúdo e gerando flashcards..."):
            cartoes = gerar_flashcards_gemini(resumo, quantidade)
            st.session_state["flashcards_gerados"] = cartoes
            st.success(f"{len(cartoes)} flashcards gerados com sucesso!")
    except ErroValidacaoIA as erro:
        st.error(str(erro))

cartoes_salvos = st.session_state.get("flashcards_gerados", [])
if cartoes_salvos:
    st.subheader("📇 Flashcards Gerados")
    for idx, card in enumerate(cartoes_salvos, start=1):
        with st.expander(f"Cartão {idx}: {card['pergunta']}", expanded=(idx == 1)):
            st.markdown(f"Resposta:")

    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter=";")
    for card in cartoes_salvos:
        writer.writerow([card["pergunta"], card["resposta"]])

    st.download_button(
        label="📥 Baixar CSV para o Anki",
        data=buffer.getvalue().encode("utf-8"),
        file_name="flashcards_datastudy.csv",
        mime="text/csv",
        use_container_width=True,
    )
