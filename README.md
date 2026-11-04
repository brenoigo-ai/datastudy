# DataStudy — Copiloto Inteligente de Estudos

Plataforma de gestão de estudos que parte da análise do app **Aprovado**
(concorrente de mercado) e propõe automações que ele não tem: edital
verticalizado com progresso automático, ciclo de estudos ponderado,
repetição espaçada (fixa ou adaptativa via SM-2), gestão de foco ativo
e notificações preditivas.

> Esta é a **segunda rodada** desta entrega: incorpora uma revisão
> técnica externa (outra IA revisou a v1). A seção **"Revisão externa
> incorporada"**, no fim deste README, mostra exatamente o que foi
> aceito, o que foi corrigido e o que foi conscientemente adiado — e
> por quê.

## Stack e por quê

| Camada | Escolha | Motivo |
|---|---|---|
| Lógica de domínio | Python 3.10+, `pydantic` v2 | validação + serialização JSON triviais (`model_dump_json`/`model_validate`), sem código repetido em cada entidade |
| Interface | Streamlit (multipage) | é o que o próprio documento do projeto pede; dashboards interativos sem escrever front-end à parte |
| Gráficos | Plotly | é o único dos três (Streamlit nativo, Matplotlib, Plotly) com pizza + barra + boa integração `st.plotly_chart` |
| Persistência | Repository Pattern — `JsonFileRepository` (padrão) e `SqliteRepository` (alternativa), atrás de um único contrato `Repository[T]` | cumpre literalmente o pedido de "persistência simulada facilmente substituível": trocar o backend é mudar uma variável de ambiente, não código |
| Testes | `pytest` + `streamlit.testing.v1.AppTest` | os serviços (lógica pura) e as páginas Streamlit (via `AppTest`, o framework oficial de testes do Streamlit) são verificados automaticamente — ver seção "Testes" |

## Arquitetura

```
datastudy/
├── app.py                          # Início/dashboard (streamlit run app.py)
├── pages/                          # páginas descobertas automaticamente pelo Streamlit
│   ├── 1_⏱️_Nova_Atividade.py      # cronômetro + foco ativo + meta de tempo + exercícios + revisão
│   ├── 2_📚_Materias_e_Edital.py   # CRUD + edital verticalizado
│   ├── 3_🔁_Revisoes.py            # fila de revisões pendentes/atrasadas (fixa + adaptativa)
│   ├── 4_🎯_Planejamento_e_Ciclo.py
│   ├── 5_📊_Desempenho.py          # gráficos (Plotly) + linha do tempo
│   └── 6_📜_Historico.py           # ver/ajustar/excluir atividades passadas
├── src/datastudy/                  # pacote instalável, agnóstico de UI
│   ├── config.py                   # fábrica de repositórios (DIP)
│   ├── domain/
│   │   ├── enums.py
│   │   └── models.py               # entidades pydantic
│   ├── repositories/
│   │   ├── base.py                 # contrato abstrato Repository[T]
│   │   ├── json_repository.py
│   │   └── sqlite_repository.py
│   ├── services/                   # um módulo por requisito funcional (ver tabela abaixo)
│   └── utils/
├── tests/                          # 28 testes automatizados (ver "Testes")
├── data/                           # onde o backend JSON grava os .json (git-ignorado)
├── pyproject.toml                  # projeto instalável (layout src)
└── .github/workflows/ci.yml        # roda a suíte a cada push/PR
```

A UI depende só de `services`; `services` depende só de `Repository[T]`
(nunca de `JsonFileRepository` diretamente) e de `domain` — nunca o
contrário. Isso é o que permite testar toda a lógica de negócio sem
subir um navegador.

## Requisito -> módulo

| # | Requisito | Onde está |
|---|---|---|
| 1 | Gestão Core (Matérias/Conteúdos) | `domain/models.py`, `services/materia_service.py` |
| 2 | Edital Verticalizado | `domain/models.py` (`Edital`/`TopicoEdital`), `services/edital_service.py` |
| 3 | Tracking de Tempo (Iniciar/Pausar/Concluir) | `services/timer_service.py` |
| 4 | Gestão de Foco Ativa | `services/timer_service.py` (`sugerir_descanso`) |
| 5 | Dashboard e Gráficos | `services/performance_service.py`, `pages/5_📊_Desempenho.py` |
| 6 | Registro de Exercícios | `domain/models.py` (`RegistroExercicio`), `services/performance_service.py` |
| 7 | Planejamento e Ciclo Inteligente | `services/planning_service.py` (`peso_efetivo`, `RoundRobinPonderadoSuave`) |
| 8 | Revisões Espaçadas Automatizadas (fixa + SM-2) | `services/spaced_repetition_service.py` |
| 9 | Notificações Inteligentes | `services/notification_service.py` |
| — | Histórico (paridade com o Aprovado) | `pages/6_📜_Historico.py` |

## O algoritmo do Ciclo de Estudos

`gerar_ciclo_estudos` não sorteia nem apenas agrupa por peso — usa
**Smooth Weighted Round Robin (SWRR)**, a mesma técnica de
balanceadores de carga (ex.: upstream do Nginx), implementada em
`RoundRobinPonderadoSuave`. Isso garante que uma matéria com peso maior
apareça proporcionalmente mais vezes, mas sempre **intercalada** com as
demais — nunca em rajada — o que bate com o comportamento descrito no
app de referência ("as matérias planejadas vão se alternando").

O peso de cada matéria (`peso_efetivo`) combina três fatores
declarados pelo usuário: peso manual, dificuldade e proporção de
questões na prova — quanto maior qualquer um dos três, mais tempo/mais
repetições a matéria recebe.

## Repetição espaçada: fixa vs. adaptativa (SM-2)

Dois modos, ambos disponíveis ao concluir uma atividade:

- **Fixa** (`criar_plano_periodico`): datas de 1/7/30 dias calculadas
  de uma vez, no momento da criação — igual ao comportamento do app de
  referência (Aprovado).
- **Adaptativa / SM-2** (`criar_plano_adaptativo` +
  `concluir_revisao_adaptativa`): só a próxima revisão existe por vez.
  A cada revisão concluída, você informa a qualidade do recall (0 a 5)
  e `calcular_sm2` decide o próximo intervalo *na hora* — erra, volta
  para 1 dia; acerta bem, o intervalo cresce (multiplicado por um fator
  de facilidade que também se ajusta). É estritamente mais inteligente
  que a fixa, ao custo de exigir uma resposta ativa do usuário a cada
  revisão em vez de zero cliques.

## Setup

```bash
pip install -e ".[dev]"          # instala o pacote + streamlit + plotly + pytest
streamlit run app.py             # abre o dashboard em http://localhost:8501
```

Para trocar o backend de persistência sem alterar código:

```bash
export DATASTUDY_BACKEND=sqlite  # padrão: "json"
export DATASTUDY_DATA_DIR=/caminho/customizado  # padrão: ./data
```

## Testes

```bash
pytest -v
```

28 testes, todos verificados nesta entrega:

- **22** cobrem os algoritmos e serviços (ponderação, round-robin,
  repetição espaçada fixa e SM-2, cronômetro/duração líquida, progresso
  automático do edital) — lógica pura, sem depender de Streamlit.
- **6** são testes de fumaça com `streamlit.testing.v1.AppTest` (o
  framework oficial de testes do Streamlit): confirmam que `app.py` e
  as 6 páginas sobem sem lançar exceção, cada um com um
  `DATASTUDY_DATA_DIR` isolado.

## O que é escopo real vs. o que é próximo passo

- **Testado de ponta a ponta**: todo o núcleo algorítmico (`services/`
  + `domain/`) e o carregamento de todas as páginas.
- **Funcional, mas testado apenas por carregamento (não por
  interação)**: os fluxos de formulário dentro de cada página (cliques
  em botões, preenchimento de campos) — `AppTest` permite simular isso
  também, mas não foi o foco desta entrega.
- **Simplificação deliberada**: a "gestão de foco ativo" mostra a
  sugestão de descanso e a duração recomendada, mas não há um
  cronômetro regressivo em tempo real na pausa — Streamlit reprocessa a
  página inteira a cada interação, então uma contagem regressiva fluida
  exigiria um componente JS customizado (fora do escopo Python puro
  pedido). Notificações são geradas sob demanda (ao abrir a página), não
  via push real.

## Revisão externa incorporada

Uma segunda IA revisou a v1 deste projeto. Avaliação ponto a ponto:

**Aceito e implementado:**
- *Linha do Tempo órfã* — correto: `linha_do_tempo()` existia em
  `performance_service.py` mas nunca era chamada por nenhuma página.
  Agora está em `pages/5`.
- *Falta de tratamento de erro no `next(...)`* — correto: se a matéria
  de uma atividade em andamento fosse excluída, `pages/1` quebraria com
  `StopIteration`. Corrigido com busca defensiva.
- *SRS estático* — o ponto mais valioso do dossiê. Implementado como um
  **segundo modo** (SM-2), sem remover o modo fixo original (que ainda
  reflete fielmente o app de referência).
- *Histórico ausente* — gap real de paridade com o Aprovado (que tem
  "Histórico" como item de menu). Adicionado em `pages/6`.

**Aceito com correção** — o código sugerido para o Histórico fazia
`atividade.status = "concluida"` (string solta) em vez de
`StatusAtividade.CONCLUIDA` (o enum). Testado empiricamente: o pydantic
*não* valida atribuição direta de atributo por padrão, então o objeto
em memória fica sem o método `.value` até a próxima leitura do
repositório — inofensivo *nesse* trecho específico (o código já dá
`st.rerun()` antes de qualquer coisa reler `.status.value`), mas é uma
armadilha real para qualquer edição futura. Corrigido usando o enum.

**Contextualizado, não implementado agora:**
- *"Falso banco de dados" (SQLite guardando JSON em coluna TEXT)* —
  verdade, e é proposital: o objetivo era ter duas implementações
  100% intercambiáveis do mesmo `Repository[T]` sem migração de schema
  por entidade. Migrar para SQLModel (colunas reais, chaves
  estrangeiras) é o próximo passo correto **se e quando** o app
  precisar de queries relacionais de verdade — não é urgente para uso
  pessoal de uma pessoa só.
- *"Full scan" em `performance_service`* — verdade em tese
  (`SELECT SUM(...)` seria mais eficiente que somar em Python), mas é
  otimização prematura na escala real deste app (milhares de registros
  no máximo, não milhões); vale revisitar junto com a migração acima,
  não antes dela.
- *`ON DELETE CASCADE`* — como o `SqliteRepository` atual não tem
  colunas/chaves estrangeiras de verdade (é JSON-em-TEXT, ver acima),
  não há o que fazer cascade *no banco* ainda; essa sugestão só faz
  sentido depois da migração para SQLModel. Até lá, o delete em cascata
  manual em `materia_service.py` é a solução correta para a arquitetura atual.
- *SQLModel/Postgres/Supabase, Flutter, FastAPI, push real* — roadmap
  legítimo de v2 caso o projeto cresça além de uso pessoal, mas fora do
  escopo desta rodada (exigem infraestrutura externa que não dá para
  validar aqui com testes automatizados).
