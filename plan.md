# Lotofácil — MVP execution plan

> Status legend: TODO / IN_PROGRESS / DONE / BLOCKED. Auditoria e entrega verificadas em 2026-10-10; evidências abaixo.

## Preflight
- [x] P00 DONE — Inspect git status, repository layout, dependencies, models, routes, migrations, test fixtures; save baseline checks (10-testing).
- [x] P01 DONE — Validate existing 18 tests (or record actual count) and document discrepancies; avoid mass import.

## Delivery path (priority order)
- [x] P02 DONE — Register `Contest` and `SyncExecution` in Django Admin, read-only audit fields (09).
- [x] P03 DONE — Harden sync behavior: reliable status/progress, proper errors, no duplication; regression tests (04).
- [x] P04 DONE — Implement deterministic statistics service and unit tests (05).
- [x] P05 DONE — Implement game generation engine, validation and tests (06).
- [x] P06 DONE — Implement rolling historical backtesting and baseline, with no look-ahead leakage (07).
- [x] P07 DONE — Expose and validate versioned HTTP contracts (08).
- [x] P08 DONE — Integrate API tests, error behavior, docs and quality gates (10, 11).

## Deferred/optional in 1–2 hour sprint
- [ ] P09 TODO — Import the full historical dataset via manually executed, rate-limited commands after review (03, 04).
- [ ] P10 TODO — Production deployment, scheduler/queue, UI, advanced optimization: out of current scope.

## Operating rules
- Read the associated spec before implementing each item; update this checklist with evidence such as test names, command output and code paths.
- Prefer a single well-tested vertical slice over unfinished breadth. If time-constrained: deliver P00–P05 first, then P06–P08.
- Write deviations and design decisions under the log below.

## Execution log / decisions
- **Initial handoff:** Existing Django + PostgreSQL, `Contest`, `SyncExecution`, Caixa imports, three result endpoints and 16 verified tests previously observed; user subsequently added two tests, but passing status of 18 has not been established in this handoff. Reinspect the actual repository.

- **Auditoria 2026-10-10:** raiz confirmada; backend Django/DRF existente, 2 migrações, 18 casos previstos. Nenhum serviço de estatísticas/geração/backtest; admin vazio. Alterações prévias em JSON/XLSX/sync_info e exclusões de specs/rules preservadas. `test_sync_history.py` contém prosa Markdown após os testes, causando SyntaxError.
- **Baseline (backend/.venv):** ruff check exit 1 (161 erros de sintaxe); format --check exit 2 (sintaxe e formatação em models/migração 0002); manage.py check exit 0 (0 issues); pytest exit 2 (erro de coleta); makemigrations --check --dry-run exit 0 (No changes detected), mas consulta de consistência ao PostgreSQL bloqueada pelo sandbox.
- **Decisões:** preservar resposta health com status/service/version; não reescrever migração 0002, excluí-la apenas do formatador. Remover prosa acidental do módulo de testes. Novas APIs: vazio=404; entradas inválidas=400; acesso público conforme DRF existente. Backtest implementará fixed_games e rolling_baseline independente de histórico; heurística aprendida opcional não implementada. Seed inteiro assinado de 64 bits. Sem alteração de dados históricos.

- **P01:** removida apenas prosa acidental, preservados os 18 testes. PostgreSQL acessível com autorização do sandbox; pytest-django: `18 passed in 0.39s`, exit 0, banco de teste isolado.

- **P02:** admin de ambos os modelos somente leitura, filtros/busca e bloqueio de inclusão/edição/exclusão. `pytest results/test_admin.py -q`: 3 passed, exit 0.

- **P03:** validação de delay finito, payloads e número positivo; normalização no clean; conclusão dentro do tratamento de falhas; erro de logging não mascara causa original. Testes de retomada, no-op, dry-run, opções, 429/timeout/conexão, payload e limite de retries. Execução intermediária detectou import incorreto (8 failed/6 errors), corrigido; suíte final desta etapa: 36 passed in 0.59s, exit 0. Concorrência de importadores e SIGKILL permanecem limitações documentadas; nenhuma migração alterada.

- **P04:** estatísticas determinísticas, validação defensiva, seleção window/as_of em uma consulta, frequências/atrasos/paridade/somas/repetições. `pytest results/test_statistics.py -q`: 7 passed in 0.23s, exit 0.

- **P05:** gerador com RNG local, seed 64 bits, até 100 jogos distintos e 10000 tentativas; validação exata de viabilidade de paridade/soma. `pytest results/test_game_generator.py -q`: 15 passed in 0.10s, exit 0.

- **P06:** fixed_games comparado a baseline de mesmo tamanho; rolling_baseline gera antes de ler dezenas-alvo, RNG local sequencial. Limites 200 concursos/100 jogos, gaps contados, métricas exatas e distribuição 0..15. Teste altera alvos/futuro e verifica jogos invariantes. `pytest results/test_backtesting.py -q`: 9 passed in 0.03s, exit 0.

- **P07:** três novas rotas integradas, serializers estritos para JSON/campos desconhecidos, 400/404 estruturados. Health e rotas existentes preservados. Bloqueio automático de HTTP externo em testes. Suíte acumulada: 95 passed in 0.68s, exit 0.

- **P08:** README substitui handoff por setup, política de acesso, contratos completos, curl, testes e limitações; requirements registra dependências diretas instaladas, sem instalar pacotes. Testes adicionais confirmam integridade de importação inválida, números defensivos, ausência de escritas pelas novas operações e limite de backtest em uma consulta.

## Validação final — 2026-10-10

Comandos executados em `backend/`, usando `.venv/bin/` (equivalente a venv ativado). PostgreSQL acessado fora da restrição inicial de rede, com aprovação do sandbox; pytest-django criou/usou seu banco isolado. Não houve importação real, migrate de desenvolvimento, criação de superusuário, exclusão de volumes, deploy ou commit.

| Gate | Resultado real | Exit |
| --- | --- | --- |
| `ruff check .` | PASS — All checks passed! | 0 |
| `ruff format --check .` | PASS — 38 files already formatted | 0 |
| `python manage.py check` | PASS — System check identified no issues (0 silenced). | 0 |
| `python -m pytest -q` | PASS — 104 passed in 0.74s; nenhum failed/skipped | 0 |
| `python manage.py makemigrations --check --dry-run` | PASS — No changes detected; sem aviso de conexão nesta execução | 0 |
| `git diff --check` (raiz) | PASS — sem saída | 0 |

### Aceitação SPEC-11

| Critério | Estado e evidência |
| --- | --- |
| Django e rotas existentes | PASS — system check; health exato, latest, detail e 404 testados |
| Testes originais e novos | PASS — 18 originais preservados, total final 104 |
| Admin inspecionável/imutável | PASS — test_admin: registro, campos readonly, acesso superuser e bloqueios |
| Sync retomável/progresso | PASS — testes originais e test_sync_regressions; falha parcial, no-op, dry-run, retomada e logging |
| Estatísticas exatas sem Caixa | PASS — test_statistics, fixture global bloqueia HTTP externo |
| Gerador válido e limitado | PASS — test_game_generator: seed, RNG global, filtros, inviabilidade, duplicatas e tentativas |
| Backtest limitado sem look-ahead | PASS — test_backtesting e limite ORM/API; alvos alterados não afetam geração |
| API e validação | PASS — test_feature_api: 200/400/404/405, JSON malformado, schemas/seleção/replay |
| Quality gates | PASS — saídas acima; exceção explícita de formatação da migração preexistente 0002 |
| README | PASS — setup, compose, venv, migrate/runserver como instruções; endpoints, curl, testes e limitações |
| Revisão de alterações | PASS — revisão dos serviços, serializers, views, comandos e testes; migrations preservadas; nenhum segredo novo ou ação destrutiva |

`git diff` não inclui arquivos ainda não rastreados: todo `backend/` já estava untracked no início. A revisão incluiu leitura direta dos arquivos implementados, além de status/diff. Credenciais locais de desenvolvimento e chave de desenvolvimento já existentes não foram alteradas nem commitadas. JSON/XLSX/sync_info e exclusões antigas de specs/rules pertenciam ao estado inicial e não foram tocados.

### Arquivos da entrega

- Atualizados: `README.md`, `plan.md`, `backend/pyproject.toml`, `backend/results/admin.py`, `models.py`, `serializers.py`, `views.py`, `urls.py`, `services/contest_service.py`, `management/commands/import_history.py`, `management/commands/sync_history.py`, `test_sync_history.py`, `test_contest_service.py`.
- Criados: `backend/requirements.txt`; `backend/results/services/statistics.py`, `game_generator.py`, `backtesting.py`; `backend/results/conftest.py`, `test_admin.py`, `test_sync_regressions.py`, `test_statistics.py`, `test_game_generator.py`, `test_backtesting.py`, `test_feature_api.py`.
- Nenhuma migração criada ou reescrita. Nenhum arquivo de histórico alterado por esta execução.

### Pendências e verificações não executadas

- P09 TODO: importação histórica em massa somente após autorização explícita. Caixa ao vivo NOT RUN; integração verificada com mocks, sem afirmar disponibilidade atual nem último concurso.
- P10 TODO / fora de escopo: deploy, scheduler/queue, frontend, otimização avançada. Setup em ambiente novo e runserver manual NOT RUN; o ambiente existente foi verificado via checks e cliente de testes.
- Limitações aceitas: importadores concorrentes podem falhar por unicidade; não há trava distribuída. SIGKILL/perda de banco pode deixar running; não há detecção automática de execução obsoleta. Erro de logging é reportado preservando a exceção original, mas banco indisponível pode impedir persistência do estado final.
- Heurística baseada em treinamento histórico é opcional e não foi implementada. Rolling baseline não recebe dados de sorteios; jogos fixos escolhidos externamente podem conter viés de seleção. Nenhuma alegação de previsão, vantagem estatística ou ganhos.
- Próxima prioridade operacional, se autorizada: revisar/importar lotes históricos P09, observando limites e logs. Não é necessária para concluir os critérios do MVP de código.
