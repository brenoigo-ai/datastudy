import json
import os
import urllib.request
from typing import Any


class ErroValidacaoIA(ValueError):
    """Erro levantado quando os parâmetros de geração de flashcards são inválidos."""


def obter_chave_gemini() -> str:
    """Busca a chave GEMINI_API_KEY nas variáveis de ambiente ou secrets do Streamlit.

    Returns:
        str: Chave configurada ou string vazia se ausente.
    """
    chave = os.getenv("GEMINI_API_KEY", "").strip()
    if chave:
        return chave
    try:
        import streamlit as st
        if "GEMINI_API_KEY" in st.secrets:
            return str(st.secrets["GEMINI_API_KEY"]).strip()
    except Exception:
        pass
    return ""


def validar_pedido_flashcards(resumo: str, quantidade: int) -> tuple[str, int]:
    """Valida o texto de entrada e a quantidade de flashcards solicitada.

    Args:
        resumo: Texto base de estudo.
        quantidade: Total de flashcards desejados (entre 1 e 15).

    Returns:
        tuple[str, int]: Texto limpo e quantidade validada.

    Raises:
        ErroValidacaoIA: Se o resumo for muito curto ou a quantidade estiver fora do limite.
    """
    texto_limpo = (resumo or "").strip()
    if len(texto_limpo) < 20:
        raise ErroValidacaoIA("O resumo deve ter pelo menos 20 caracteres.")
    if not isinstance(quantidade, int) or quantidade < 1 or quantidade > 15:
        raise ErroValidacaoIA("A quantidade deve ser um número inteiro entre 1 e 15.")
    return texto_limpo, quantidade


def extrair_json_flashcards(texto_resposta: str) -> list[dict[str, str]]:
    """Converte e valida o JSON retornado pelo modelo em lista de flashcards.

    Args:
        texto_resposta: String JSON retornada pela API.

    Returns:
        list[dict[str, str]]: Lista contendo dicionários com 'pergunta' e 'resposta'.

    Raises:
        ErroValidacaoIA: Se o JSON for inválido ou não contiver os campos esperados.
    """
    try:
        dados: Any = json.loads(texto_resposta)
    except json.JSONDecodeError as exc:
        raise ErroValidacaoIA("A resposta da IA não retornou um JSON válido.") from exc

    if not isinstance(dados, list) or not dados:
        raise ErroValidacaoIA("A resposta da IA deve ser uma lista não vazia de flashcards.")

    resultado: list[dict[str, str]] = []
    for item in dados:
        if not isinstance(item, dict):
            continue
        pergunta = str(item.get("pergunta", "")).strip()
        resposta = str(item.get("resposta", "")).strip()
        if pergunta and resposta:
            resultado.append({"pergunta": pergunta, "resposta": resposta})

    if not resultado:
        raise ErroValidacaoIA("Nenhum flashcard válido foi encontrado na resposta.")
    return resultado


def gerar_flashcards_gemini(resumo: str, quantidade: int = 5, api_key: str | None = None) -> list[dict[str, str]]:
    """Gera flashcards de estudo a partir de um resumo usando a API do Google Gemini.

    Args:
        resumo: Texto ou anotação de aula/apostila.
        quantidade: Número de flashcards a gerar (1 a 15).
        api_key: Chave opcional; se omitida, busca do ambiente.

    Returns:
        list[dict[str, str]]: Lista de flashcards com 'pergunta' e 'resposta'.

    Raises:
        ErroValidacaoIA: Se a entrada for inválida, a chave estiver ausente ou a API falhar.
    """
    texto_limpo, qtd = validar_pedido_flashcards(resumo, quantidade)
    chave = (api_key or obter_chave_gemini()).strip()
    if not chave:
        raise ErroValidacaoIA("Chave GEMINI_API_KEY não configurada nas variáveis de ambiente.")

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={chave}"
    prompt = (
        f"Atue como professor universitário e examinador de concursos de TI. "
        f"Extraia {qtd} flashcards objetivos do texto abaixo. "
        f"Retorne APENAS um array JSON válido no formato: "
        f'[{{"pergunta": "...", "resposta": "..."}}]\n\nTexto:\n{texto_limpo}'
    )

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.2,
            "responseMimeType": "application/json",
        },
    }

    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            corpo = json.loads(resp.read().decode("utf-8"))
            texto_json = corpo["candidates"][0]["content"]["parts"][0]["text"]
            return extrair_json_flashcards(texto_json)
    except ErroValidacaoIA:
        raise
    except Exception as exc:
        raise ErroValidacaoIA(f"Falha ao comunicar com a API Gemini: {exc}") from exc
