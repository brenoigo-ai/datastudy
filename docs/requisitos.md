# Requisitos e Critérios de Aceite — DataStudy

## 1. Requisitos Funcionais (RF)
| ID | Descrição |
| :--- | :--- |
| **RF01** | Cadastrar matérias e tópicos do edital com peso e prioridade. |
| **RF02** | Registrar sessões de estudo (horas líquidas, questões certas e erradas). |
| **RF03** | Agendar e concluir revisões espaçadas automaticamente. |
| **RF04** | Gerar e rebalancear o ciclo semanal de estudos conforme horas disponíveis. |
| **RF05** | Visualizar indicadores e gráficos de desempenho por matéria e evolução temporal. |
| **RF06** | Filtrar, buscar e auditar o histórico de atividades registradas. |

## 2. Requisitos Não Funcionais (RNF)
| ID | Descrição |
| :--- | :--- |
| **RNF01** | Persistência permanente em banco de dados local (SQLite / JSON estruturado). |
| **RNF02** | Interface web responsiva (Streamlit) compatível com desktop e dispositivos móveis. |
| **RNF03** | Regras de negócio desacopladas da camada de interface e cobertas por testes automatizados (pytest). |
| **RNF04** | Consultas parametrizadas e ausência de chaves/segredos expostos no código-fonte. |

## 3. Histórias de Usuário e Critérios de Aceite (Dado / Quando / Então)

### US01 — Registro de Estudo com Validação
> **Como** estudante de concursos e graduação, **quero** registrar meus blocos de estudo e questões, **para** acompanhar minha taxa de acerto real.
* **Caminho Feliz:** **Dado** que selecionei uma matéria válida e informei 50 minutos e 10 questões, **Quando** clico em salvar atividade, **Então** o sistema grava a sessão no banco e atualiza as métricas.
* **Caso de Erro:** **Dado** que informei um número de acertos maior que o total de questões resolvidas, **Quando** tento validar o registro, **Então** o sistema rejeita a operação com erro de validação e nada é gravado no banco.

### US02 — Gestão de Edital e Matérias
> **Como** estudante organizado, **quero** cadastrar disciplinas e tópicos com pesos específicos, **para** priorizar matérias mais importantes no ciclo.
* **Caminho Feliz:** **Dado** que preenchi o nome da matéria e o peso de 1 a 5, **Quando** confirmo o cadastro, **Então** a matéria passa a listar no edital e no gerador de ciclo.
* **Caso de Erro:** **Dado** que deixei o nome da matéria em branco, **Quando** tento salvar, **Então** o sistema bloqueia o cadastro e exibe mensagem de campo obrigatório.

### US03 — Controle de Revisões Espaçadas
> **Como** estudante, **quero** visualizar e concluir as revisões pendentes do dia, **para** evitar a curva do esquecimento.
* **Caminho Feliz:** **Dado** que possuo uma revisão agendada para hoje, **Quando** marco a revisão como concluída, **Então** seu status é atualizado permanentemente no repositório.

## 4. Escopo Fora do MVP
* Login multiusuário e autenticação OAuth.
* Aplicativo nativo compilado para iOS/Android (uso via Web App responsivo).
* Cobrança ou gateway de pagamentos.
