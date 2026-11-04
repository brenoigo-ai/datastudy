"""Testes de fumaça com `streamlit.testing.v1.AppTest`: garantem que
cada página sobe sem lançar exceção, usando um diretório de dados
isolado por teste (via `DATASTUDY_DATA_DIR`)."""

import glob
import os

import pytest
from streamlit.testing.v1 import AppTest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGINAS = ["app.py", *sorted(glob.glob(os.path.join(RAIZ, "pages", "*.py")))]


@pytest.mark.parametrize("caminho", PAGINAS)
def test_pagina_carrega_sem_excecao(tmp_path, monkeypatch, caminho):
    monkeypatch.setenv("DATASTUDY_DATA_DIR", str(tmp_path))
    caminho_absoluto = caminho if os.path.isabs(caminho) else os.path.join(RAIZ, caminho)
    at = AppTest.from_file(caminho_absoluto)
    at.run(timeout=15)
    assert not at.exception

