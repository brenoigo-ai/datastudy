"""DataStudy — copiloto inteligente de estudos.

Pacote raiz. A árvore é organizada em camadas (Clean Architecture-lite):

    domain/        entidades e regras de negócio puras (sem I/O)
    repositories/  contrato de persistência + implementações (JSON, SQLite)
    services/      casos de uso (algoritmos, orquestração)
    utils/         utilidades genéricas (ids, formatação de datas)

A camada de UI (Streamlit) mora fora do pacote, em app.py e pages/, e
depende apenas de `services` — nunca o contrário.
"""

__version__ = "0.1.0"
