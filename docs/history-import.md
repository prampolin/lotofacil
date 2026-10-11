# P10 — Diagnóstico e plano de importação histórica

Data: 2026-10-10 (America/Sao_Paulo). **P10.1 concluído: único lote autorizado 233–257 importado e verificado. Restante do histórico não autorizado.**

## Diagnóstico real, sem escrita

Consulta ao PostgreSQL configurado no backend, dentro de `transaction.atomic()` com `SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY`; `SHOW transaction_read_only` retornou `on`. A conexão inicial foi impedida pelo sandbox (exit 1); repetição com acesso autorizado terminou em exit 0. Nenhuma migration ou escrita foi executada no banco de desenvolvimento.

| Verificação | Resultado |
| --- | --- |
| Concursos armazenados | 241 |
| Intervalo mínimo–máximo | 1–3800 |
| Faixas presentes | 1–232 (232 registros), 3792–3800 (9 registros) |
| Lacuna interna | 233–3791: 3559 concursos |
| Último número publicado informado pela Caixa | 3801 |
| Ausentes até o último informado | 233–3791 e 3801: 3560 |
| Cobertura numérica | 241 / 3801 × 100 = **6,34%** |
| Números duplicados | 0 |
| Registros inválidos segundo validação do modelo | 0 |
| Listas de dezenas desordenadas | 0 |
| Datas posteriores a 2026-10-10 | 0 |
| SyncExecution | 1, completed, concursos 230–232, processed=3, sem erro |

A leitura percorreu todos os registros e executou `full_clean(validate_unique=False, validate_constraints=False)` em instâncias em memória, sem save; duplicação foi conferida separadamente pela cardinalidade dos números. Dezenas: lista de 15 inteiros distintos entre 1 e 25, ordenação conferida no valor original; número positivo e campos/data validados. Não houve comparação de cada resultado com a Caixa: integridade estrutural não comprova exatidão contra a origem. Sorteios diferentes podem legitimamente compartilhar dezenas; isso não é duplicação de concurso.

Impressão SHA-256 do snapshot de todos os campos de Contest, ordenado por number e serializado com `json.dumps(rows, default=str, sort_keys=True)`:

`304a4d017deebd3d34ec6fbddb348558ba9eafacc7f03e1185a55ab177cc7ad9`

Foi realizada uma única consulta HTTP à [API oficial da Caixa](https://servicebus2.caixa.gov.br/portaldeloterias/api/lotofacil), pelo próprio dry-run de sync_history, sem importar o resultado. O último número é um snapshot, não garantia de estabilidade futura ou de disponibilidade de cada endpoint histórico. Cobertura assume numeração contínua de 1 ao último publicado.

## Dry-run executado

Equivalente ao comando abaixo, chamado via `call_command` dentro da transação READ ONLY:

```sh
cd backend
.venv/bin/python manage.py sync_history --start 1 --batch-size 25 --limit 25 --delay 2 --dry-run
```

Saída real:

```text
Último concurso informado: 3801
Concursos existentes: 241
Concursos ausentes: 3560
Concursos selecionados: 25
Simulação concluída. Nenhum dado foi alterado.
```

Igualdade exata de todos os campos de Contest e SyncExecution antes/depois confirmada, além da proteção READ ONLY. Primeiro lote calculado a partir das lacunas: **233–257**. O comando imprime a quantidade selecionada, não a lista. Esse dry-run ocorreu antes da correção das pausas; as correções afetam apenas a execução real, verificada com mocks, sem nova consulta desnecessária à origem.

## Revisão e correções dos importadores

| Comando | Comportamento verificado |
| --- | --- |
| import_contests | Uma requisição, timeout=20s, valida payload e número solicitado. Cria ou atualiza por número; idempotência de identidade, mas pode substituir resultado existente. Não usar diretamente para esta operação de preservação. Não cria SyncExecution sozinho. |
| import_history | Intervalo de até 100, ignora existentes, até 3 tentativas por concurso; transitórios: 429, 5xx, timeout/conexão. Erros permanentes interrompem imediatamente. Não cria SyncExecution sozinho. |
| sync_history | Seleciona somente ausentes, em ordem crescente; limit/batch-size entre 1 e 100; um SyncExecution por execução real. Atualiza processed após cada retorno bem-sucedido e grava completed/failed, finished_at e erro. Retomada consulta novamente ausentes; dry-run/no-op não criam log. Consulta latest falha sem retry e antes de criar log. |

Defeitos corrigidos: pausa entre consulta latest e primeira importação; propagação de delay ao importador interno; retries agora aguardam `max(delay, 2)` e `max(delay, 4)` segundos. Isso preserva o intervalo mínimo mesmo com delay maior que o backoff. Não houve mudança de argumentos CLI, endpoints, modelos ou migrations.

Limitações relevantes:

- Timeout de requests=20s não é prazo total rígido da execução. Não há quota oficial ou SLA identificado na resposta desta consulta; delay=2s é política conservadora local, não autorização da Caixa nem garantia contra bloqueio.
- Retry-After não é interpretado. 429 pode receber até 3 tentativas internas; 403/permanentes interrompem imediatamente. Após falha/restrição da origem, não reiniciar automaticamente nem tentar outro lote. Reavaliar acesso e prazo informado pela origem antes de retomar.
- Não há loop infinito: três tentativas por concurso, no máximo 100 selecionados por execução. batch-size agrupa a saída, não adiciona cooldown entre grupos nem altera limit.
- Não executar importadores concorrentes. Sem trava distribuída; concorrência pode gerar corrida e o importador unitário pode atualizar dados existentes.
- Salvamento do concurso e progresso não são uma única transação. SIGKILL/KeyboardInterrupt pode deixar running ou progresso defasado; retomada usa Contest, não o contador. Banco indisponível pode impedir persistência de falha; erro adicional é reportado sem mascarar o original. Não há log de cada tentativa HTTP nem detecção automática de execução obsoleta.
- Falha na consulta latest acontece antes do log persistente; guardar também saída do terminal. Não se afirma auditoria completa de tentativas apenas por SyncExecution.

## Plano concreto sujeito à autorização

1. Um único operador/processo, lote inicial de **25 concursos (233–257)**. Comando abaixo, **ainda não executado**:

   ```sh
   cd backend
   .venv/bin/python manage.py sync_history --start 1 --batch-size 25 --limit 25 --delay 2
   ```

2. Após cada execução: revisar exit code, SyncExecution, processed, estado e erro; confirmar registros novos válidos, ausência de duplicatas e preservação de todos os campos dos concursos anteriores. Aguardar pelo menos 2 segundos antes da próxima execução. Não iniciar novo lote se houver falha, bloqueio, execução running não esclarecida ou divergência de integridade.
3. Após autorização para o restante, repetir o mesmo comando em execuções controladas; reconsulta de ausentes oferece retomada sem apagar/reimportar existentes. Não há shell loop automático preparado.
4. Interromper na primeira execução que falhar (incluindo esgotamento das 3 tentativas internas), preservar progresso e registrar causa disponível. Bloqueio percebido pelo operador também exige interrupção e revisão, sem contorno do bloqueio.
5. Ao terminar: repetir diagnóstico READ ONLY contra latest, conferir lacunas, integridade, duplicações e preservação do snapshot inicial; executar gates; registrar números reais, logs e falhas neste documento e em plan.md. Novos sorteios durante o processo exigem recalcular o escopo.

Estimativas para o snapshot, excluindo o dry-run já realizado:

- Primeiro lote: **26 chamadas** sem retry (1 latest + 25 detalhes); até 76 se cada detalhe consumir 3 tentativas e tiver sucesso na terceira.
- Histórico completo: **143 execuções** (142 × 25 + 10), **3703 chamadas** sem retry (3560 detalhes + 143 latest). Teto aritmético de 10823 se todos consumirem 3 tentativas; não é autorização para insistir diante de falhas.
- Pausas internas mínimas: 3560 × 2s = 1h58min40s. Com 142 intervalos externos de 2s: **2h03min24s**, mais latência HTTP/DB, revisões e eventuais retries. Não é previsão de duração garantida.

## Evidências de qualidade

Executados em backend com `.venv/bin/`, após as correções:

| Comando | Saída real | Exit |
| --- | --- | --- |
| python -m pytest results/test_import_contests.py results/test_import_history.py results/test_sync_history.py results/test_sync_regressions.py -q | 32 passed in 1.36s | 0 |
| ruff check . | All checks passed! | 0 |
| ruff format --check . | 39 files already formatted | 0 |
| python manage.py check | System check identified no issues (0 silenced). | 0 |
| python -m pytest -q | 118 passed in 1.95s | 0 |

Testes usam banco isolado pytest-django e bloqueio global de HTTP externo; mocks da Caixa. Três casos adicionais apenas para as correções: dois cenários de backoff/intervalo e um de ordem latest → pausa → importação, inclusive entre grupos. Testes existentes de idempotência, retomada, erros permanentes e limite de retries continuam aprovados.

**Estado ao encerrar a preparação P10:** fase 4 ainda não executada naquele momento. A execução posterior autorizada P10.1 está registrada abaixo.


## P10.1 — Execução real concluída

Em 2026-10-10, das 20:47:42 às 20:48:46 (America/Sao_Paulo), executado **um único lote**, via `call_command("sync_history", start=233, batch_size=25, limit=25, delay=2)`, equivalente ao CLI existente. Exit 0. Nenhum lote seguinte iniciado ou autorizado.

Preflight: PostgreSQL 17.11 acessível, 241 concursos, nenhum no intervalo 233–257, nenhuma execução running. A primeira tentativa de conexão foi negada pelo sandbox (exit 1); repetição autorizada bem-sucedida. Snapshot integral salvo antes da importação; conferido novamente imediatamente antes do comando.

Um invólucro operacional temporário limitou as URLs à consulta latest e aos 25 detalhes autorizados, mediu/garantiu intervalo mínimo de 2 segundos e interromperia imediatamente em 403/429. Os comandos existentes executaram seleção, validação, persistência, retry/backoff e SyncExecution; nenhum código de produção foi alterado. Não ocorreram retries ou bloqueios.

| Verificação | Resultado |
| --- | --- |
| Importados | 233–257 inclusive: 25 |
| Falhas / retries | 0 / 0 |
| HTTP | 26 respostas 200 (latest + 25 detalhes) |
| Menor intervalo entre inícios das requisições | 2,242 segundos |
| SyncExecution | id=2, completed, processed=25, finished_at preenchido, erro vazio |
| Total antes → depois | 241 → 266 |
| Registros anteriores alterados/removidos | 0; igualdade de todos os campos dos 241 registros |
| Log anterior | Preservado integralmente |
| Duplicações / inválidos / dezenas desordenadas | 0 / 0 / 0 |
| Conferência contra respostas Caixa | Datas e dezenas dos 25 novos concursos coincidem exatamente após normalização |
| Faixas presentes | 1–257 e 3792–3800 |
| Último informado nesta execução | 3801 |
| Lacunas | 258–3791 e 3801: 3535 ausentes |
| Cobertura atualizada | 266 / 3801 = 6,9982% (7,00%) |

Verificação posterior em transação READ ONLY, exit 0. Todos os 266 registros passaram na validação do modelo; sem datas futuras. Snapshot anterior SHA-256: `304a4d017deebd3d34ec6fbddb348558ba9eafacc7f03e1185a55ab177cc7ad9`.

Evidências persistentes em [p10-1/](history-import/p10-1/): `before.json`, `after.json`, `http.json` (horários/status/payloads reais), `execution.log`, `verification.json` e `pytest.log`. O banco mantém também SyncExecution id=2. Não houve consultas HTTP adicionais para a conferência.

Gates em backend, todos exit 0: `ruff check .` → All checks passed!; `ruff format --check .` → 39 files already formatted; `python manage.py check` → System check identified no issues (0 silenced).; `python -m pytest -q` → **118 passed in 1.99s**. Pytest-django usou banco de testes isolado e HTTP mockado. Gates executados durante o lote, sem alteração de código; a validação final do banco ocorreu após a conclusão.

**Encerrado após este lote.** Histórico completo permanece pendente; qualquer próxima importação requer nova autorização.
