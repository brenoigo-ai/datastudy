import pytest
from datastudy.services.ai_flashcards import (
    ErroValidacaoIA,
    extrair_json_flashcards,
    gerar_flashcards_gemini,
    validar_pedido_flashcards,
)


def test_validar_pedido_flashcards_caminho_feliz():
    texto, qtd = validar_pedido_flashcards("Resumo completo sobre normalização de banco de dados 1FN 2FN 3FN.", 5)
    assert qtd == 5
    assert "normalização" in texto


def test_validar_pedido_rejeita_resumo_curto():
    with pytest.raises(ErroValidacaoIA, match="pelo menos 20 caracteres"):
        validar_pedido_flashcards("Muito curto", 5)


@pytest.mark.parametrize("qtd_invalida", [0, -1, 16, 100])
def test_validar_pedido_rejeita_quantidade_fora_da_borda(qtd_invalida):
    with pytest.raises(ErroValidacaoIA, match="entre 1 e 15"):
        validar_pedido_flashcards("Texto válido com mais de vinte caracteres para teste.", qtd_invalida)


def test_extrair_json_flashcards_valido():
    bruto = '[{"pergunta": "O que é 1FN?", "resposta": "Atributos atômicos."}]'
    resultado = extrair_json_flashcards(bruto)
    assert len(resultado) == 1
    assert resultado[0]["pergunta"] == "O que é 1FN?"


def test_extrair_json_invalido_levanta_erro():
    with pytest.raises(ErroValidacaoIA, match="JSON válido"):
        extrair_json_flashcards("texto sem formato json")


def test_gerar_flashcards_sem_chave_levanta_erro(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    with pytest.raises(ErroValidacaoIA, match="GEMINI_API_KEY"):
        gerar_flashcards_gemini("Texto longo o suficiente para passar na validação inicial.", 3, api_key="")
