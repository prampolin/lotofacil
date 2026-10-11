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

- [x] P09 DONE — Validação integrada do MVP: gates, PostgreSQL/migrations, contratos HTTP em banco isolado, limites, replay, ausência de look-ahead e relatório docs/mvp-validation.md.

## Deferred/optional in 1–2 hour sprint
- [ ] OP01 TODO — Import the full historical dataset via manually executed, rate-limited commands after review (03, 04).
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

- OP01 TODO: importação histórica em massa somente após autorização explícita. Caixa ao vivo NOT RUN; integração verificada com mocks, sem afirmar disponibilidade atual nem último concurso.
- P10 TODO / fora de escopo: deploy, scheduler/queue, frontend, otimização avançada. Setup em ambiente novo e runserver manual NOT RUN; o ambiente existente foi verificado via checks e cliente de testes.
- Limitações aceitas: importadores concorrentes podem falhar por unicidade; não há trava distribuída. SIGKILL/perda de banco pode deixar running; não há detecção automática de execução obsoleta. Erro de logging é reportado preservando a exceção original, mas banco indisponível pode impedir persistência do estado final.
- Heurística baseada em treinamento histórico é opcional e não foi implementada. Rolling baseline não recebe dados de sorteios; jogos fixos escolhidos externamente podem conter viés de seleção. Nenhuma alegação de previsão, vantagem estatística ou ganhos.
- Próxima prioridade operacional, se autorizada: revisar/importar lotes históricos OP01, observando limites e logs. Não é necessária para concluir os critérios do MVP de código.

## P09 — Validação integrada (2026-10-10)

- IN_PROGRESS. O identificador P09 passa a representar a validação solicitada; a importação histórica opcional foi renomeada OP01 e continua não autorizada. Baseline Git limpo. Somente leituras no PostgreSQL de desenvolvimento; fixtures e mutations restritas ao banco pytest-django.

- **DONE — READY para o MVP local.** Relatório: `docs/mvp-validation.md`. 11 testes de integração novos, sem alteração funcional: fluxo geração → fixed_games, replay, mutação de resultados/futuro, banco isolado e migrations, consultas/limites, JSON e métodos.
- Baseline sandbox: 71 passed / 33 errors / 1 warning (2.80s, exit 1), conexão PostgreSQL bloqueada. Repetição autorizada: 104 passed in 0.79s, exit 0. Focado P09: 11 passed in 0.45s, exit 0.
- Gates finais em backend: `ruff check .` → All checks passed!; `ruff format --check .` → 39 files already formatted; `python manage.py check` → 0 issues; `python -m pytest -q --durations=5` → 115 passed in 0.93s. Todos exit 0.
- `makemigrations --check --dry-run` → No changes detected; `showmigrations --plan` → 20 [X]; `migrate --check` → sem saída. Todos exit 0, nenhuma migration aplicada ao desenvolvimento. Inspeção READ ONLY: PostgreSQL 17.11, lotofacil, 241 concursos/1 execução, zero migrations pendentes. Teste confirma uso de test_lotofacil e índice único.
- Cenário máximo: estatísticas 1000 + backtest 200×100, duas consultas limitadas, 0.093s local, resposta backtest 936446 bytes. Sem benchmark concorrente/SLA.
- Ajustes documentais: P09 opcional antigo renomeado OP01; SPEC-08 registra contrato confirmado e README delimita 405 às views DRF. Nenhum defeito funcional reproduzido ou correção de produção efetuada. Sem importação real, alteração de dados de desenvolvimento, migration reescrita ou deploy. Limitações/NOT RUN no relatório.
- Revisão final de diff e arquivos novos concluída; `git diff --check` exit 0. Arquivos: README.md, plan.md, specs/08-rest-api.md, docs/mvp-validation.md e backend/results/test_mvp_integration.py.

## P10 — Sincronização e validação do histórico (2026-10-10)

- **IN_PROGRESS** — diagnóstico somente leitura, revisão dos três importadores e dry-run; importação em massa exige autorização explícita posterior. P10 passa a identificar esta tarefa; a antiga referência a P10 para deploy/infra permanece apenas histórica e fora de escopo. Alterações preexistentes de P09 preservadas (README, plan, SPEC-08, teste integrado e docs).
- Diagnóstico READ ONLY + dry-run reais: 241 concursos, faixas 1–232 e 3792–3800, último Caixa=3801, 3560 ausentes; zero inválidos/duplicados/desordenados. Sandbox inicial negou TCP (exit 1); repetição com acesso autorizado exit 0. Nenhuma escrita, igualdade exata dos registros/logs antes/depois.
- Correção necessária antes da execução: `sync_history` não aguardava entre latest e primeira importação; não propagava delay ao importador interno; retry de `import_history` usava 2/4s mesmo se delay maior. Preservar argumentos e contratos, acrescentando pausa inicial e respeitando `max(delay, backoff)` em retries. Testes existentes de mocks serão adaptados para o argumento propagado; regressões focadas adicionadas apenas para estes defeitos.
- **Fases 1–2 verificadas; fase 3 dry-run concluído.** Relatório `docs/history-import.md`: cobertura 6,34%, lacunas 233–3791 e 3801; plano de 143 execuções de até 25, delay=2s, 3703 chamadas sem retries. Uma única consulta real à Caixa; nenhuma importação/escrita no PostgreSQL de desenvolvimento.
- Correções implementadas: pausa após latest, propagação de delay e backoff respeitando delay. Testes focados: `32 passed in 1.36s`, exit 0; três casos novos de regressão. Mocks existentes ajustados ao argumento interno adicional.
- Gates finais: `ruff check .` → All checks passed!; `ruff format --check .` → 39 files already formatted; `python manage.py check` → 0 issues; `python -m pytest -q` → 118 passed in 1.95s; todos exit 0. PostgreSQL de testes isolado, HTTP mockado. Nenhuma migration alterada.
- **P10 permanece IN_PROGRESS, aguardando autorização explícita para importação em massa.** Execução real e validação pós-importação NOT RUN. Limitações de Retry-After, concorrência, interrupção abrupta, latest sem log e indisponibilidade do banco detalhadas no relatório. Não marcar histórico como completo.
- Revisão final do diff funcional e do relatório concluída; `git diff --check` exit 0. Bytecode rastreado modificado pela execução dos testes restaurado ao conteúdo inicial; mudanças preexistentes de P09 preservadas.

## P10.1 — Primeiro lote real controlado (2026-10-10)

- **DONE** — autorização limitada aos concursos 233–257, até 25, intervalo mínimo 2s. Verificar PostgreSQL e snapshot integral antes; usar comandos existentes com retry/backoff, logs persistentes e interromper em bloqueios/falhas permanentes. Nenhum lote seguinte autorizado.

- Executado um único `sync_history --start 233 --batch-size 25 --limit 25 --delay 2` via call_command, exit 0; proteção operacional de escopo/intervalo e parada imediata em 403/429, sem modificar comandos. 26 HTTP 200; intervalo mínimo observado 2,242s; zero falhas/retries. SyncExecution id=2 completed, processed=25, 20:47:42–20:48:46 America/Sao_Paulo.
- PostgreSQL 17.11 confirmado após bloqueio inicial de sandbox (exit 1; repetição autorizada exit 0). Antes: 241 registros, intervalo vazio, nenhum running. Depois: 266, concursos 233–257 completos; 241 anteriores e log anterior integralmente preservados. Validação READ ONLY exit 0: zero duplicações/inválidos/desordenados, datas/dezenas novas iguais aos payloads Caixa. Cobertura 266/3801=7,00%; lacunas 258–3791 e 3801 (3535).
- Gates reais, todos exit 0: Ruff check → All checks passed!; Ruff format --check → 39 files already formatted; manage.py check → 0 issues; pytest → 118 passed in 1.99s (banco isolado, HTTP mockado). Executados durante o lote; verificação final PostgreSQL após conclusão.
- Relatório atualizado: docs/history-import.md; snapshots, saída do comando, payloads/horários HTTP, verificação e pytest persistidos em docs/history-import/p10-1/. Nenhuma alteração de código/migration, deploy ou lote adicional. P10 global permanece incompleto; próximas importações exigem nova autorização.

## P11 — Segurança, performance e estabilidade

- **DONE** — auditoria de configuração, payloads, consultas e concorrência. Sem importações reais, deploy ou escrita no histórico de desenvolvimento; testes e benchmarks no banco pytest-django, Caixa mockada. Alterações anteriores preservadas.
- Decisões: manter endpoints públicos e contratos de sucesso. Configuração por ambiente, perfil de produção fail-closed e segredos locais ignorados pelo Git; não reescrever histórico Git nem rotacionar credenciais do PostgreSQL sem coordenação. Limitar tamanho HTTP antes do parsing, documentando 413 para excesso. Serializar comandos de importação com advisory lock PostgreSQL reentrante no mesmo contexto; concorrente falha antes de HTTP. Interrupção controlada deve persistir failed; SIGKILL exige inspeção manual. Não adicionar índices sem evidência.

- Relatório: `docs/security-performance.md`; evidências em `docs/p11/`. Configuração por ambiente, DEBUG=false padrão, production fail-closed + TLS/cookies/HSTS/SMTP, payload API limitado a 64 KiB (413), advisory lock reentrante nos três importadores, logging de KeyboardInterrupt, seleção de lacunas limitada e cache combinatório imutável. API pública, CLI e sucesso REST preservados; 413 documentado em SPEC-08.
- Baseline: sandbox 71 passed/47 errors/1 warning (4.11s), TCP bloqueado; repetição autorizada 118 passed in 2.01s. Intermediários: 42 passed/1 failed (SMTP corrigido); 8 passed/3 failed (import de timezone introduzido na edição e corrigido); depois 133 passed. Final: **136 passed in 3.13s**, exit 0. 18 casos novos; concorrência via conexões independentes e Caixa mockada.
- Gates finais, exit 0: Ruff check All checks passed!; format 44 files already formatted; Django check e check --deploy production 0 issues; makemigrations --check --dry-run No changes detected; migrate --check sem saída (sem aplicar migrations). Logs de cada gate final em docs/p11/gates.log.
- Performance local, 4000 fixtures/3 repetições: medianas estatísticas 1/100/1000 = 0,754/1,560/9,293 ms (1 SQL); geração 100 = 0,656 ms (0 SQL); filtro raro = 30,719 ms/400 limitado; backtest 10×10/200×100 = 1,876/82,840 ms (1 SQL), teto 936446 bytes. Cache frio/quente 5,918/0,309 ms, resposta idêntica. EXPLAIN usa índice único existente; sem índices novos.
- Preservação READ ONLY confirmada: 266 concursos/2 logs, igualdade integral antes/depois, SHA-256 combinado 38768cb313e1f9925710b66402b155feb445cec6a46efcf6f94ca40d93dce308. Zero importações reais/deploy/migrations, nenhum histórico alterado. Removido somente bytecode de settings com segredos; demais mudanças anteriores preservadas.
- Riscos pendentes: segredos antigos no histórico Git (sem reescrita/commit/rotação do banco), rate limiting/proxy/HTTPS/backup/roles de produção, Retry-After ignorado, latest sem log persistente, SIGKILL pode deixar running, locks requerem conexão direta/pooling de sessão. P12 não especificado: pronto para próxima etapa local, **não para deploy**. Carregar .env privado no shell; README atualizado.
- Revisão final dos diffs e arquivos novos concluída; `git diff --check` exit 0. README/spec de API documentam ambiente e 413; relatório diferencia gates de código de prontidão operacional. Nenhuma etapa futura foi iniciada.
