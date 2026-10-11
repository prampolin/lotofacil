# P09 — Validação integrada do MVP Lotofácil

Data: 2026-10-10. Decisão: **READY para o MVP local definido em SPEC-11**. Não é autorização nem avaliação de prontidão para produção.

## Escopo e método

Repositório confirmado por `git rev-parse --show-toplevel`: `/Users/vitorprampolin/prampolin/lotofacil`. Estado Git inicial limpo. Foram lidos AGENTS.md, plan.md, README e SPEC-00–11; revisados modelos, migrations, serializers, views, serviços e testes existentes. Nenhum código funcional ou migration precisou ser alterado. Foram acrescentados 11 testes em `backend/results/test_mvp_integration.py`.

As requisições passaram pelo APIClient do DRF, URL resolver, middleware, serializers, serviços, ORM e renderização JSON. Não houve servidor HTTP TCP, navegador ou teste de proxy. Fixtures e alterações de resultados ocorreram exclusivamente no PostgreSQL `test_lotofacil`, criado/migrado e descartado pelo pytest-django. Um novo teste confirma `current_database()`, backend PostgreSQL, índice único de Contest.number, consistência do histórico e ausência de migrations pendentes no banco de testes. A fixture global bloqueia requests externos; Caixa foi simulada pelos testes existentes.

## Evidências de execução

Comandos em `backend/`, executáveis de `.venv/bin/` (equivalente à ativação do ambiente):

| Comando/check | Saída efetiva | Exit |
| --- | --- | --- |
| Baseline `python -m pytest -q`, dentro do sandbox | 71 passed, 1 warning, 33 errors in 2.80s; conexão local bloqueada com Operation not permitted | 1 |
| Baseline repetido com acesso autorizado: `python -m pytest -q --tb=short` | 104 passed in 0.79s | 0 |
| `python -m pytest results/test_mvp_integration.py -q -s --tb=short` | 11 passed in 0.45s | 0 |
| `ruff check .` final | All checks passed! | 0 |
| `ruff format --check .` final | 39 files already formatted | 0 |
| `python manage.py check` final | System check identified no issues (0 silenced). | 0 |
| `python -m pytest -q --durations=5` final | 115 passed in 0.93s; nenhum skipped/failed | 0 |
| `python manage.py makemigrations --check --dry-run` | No changes detected | 0 |
| `python manage.py showmigrations --plan` | 20 migrations marcadas [X], incluindo results.0001 e results.0002 | 0 |
| `python manage.py migrate --check` | Sem saída; nenhuma migration aplicada pelo comando | 0 |
| Inspeção PostgreSQL com SET TRANSACTION READ ONLY | banco lotofacil; PostgreSQL 17.11; transaction_read_only=on; pending_migrations=0; 241 Contest e 1 SyncExecution | 0 |

Uma chamada inicial do formatador usou o caminho da venv relativo à raiz e terminou em exit 127; foi corrigida para o diretório backend e executada com sucesso. A migration preexistente 0002 continua excluída somente do formatador conforme decisão P00–P08; não foi reescrita. Os números de registros acima são uma observação local, não verificação de completude histórica ou atualização contra a Caixa.

## Endpoints realmente exercitados

Todos os caminhos abaixo usam `/api/v1/` e respostas JSON verificadas nos testes existentes e novos.

| Método e caminho | Casos e resultados verificados |
| --- | --- |
| GET health/ | Corpo status/service/version preservado |
| GET results/latest/ | 200, maior número independente da ordem de inserção, chaves number/draw_date/numbers; banco vazio 404; POST 405 |
| GET results/5/ e results/2/ | 200 com data ISO e dezenas exatas; ausente 404; POST em results/1/ 405 |
| GET statistics/ | 200, window/as_of, janela incompleta e lacunas, somas/frequências/repetições, nunca observado=null; vazio 404; query inválida/desconhecida 400; dado inválido 400; POST 405 |
| POST games/generate/ | 200, replay com seed e constraints, 100 jogos distintos, zero SQL; tipos/quantidades/seed/filtros inválidos 400; JSON malformado 400; GET 405 |
| POST backtests/ | 200 nos dois modos, jogos gerados reaproveitados em fixed_games, acertos calculados independentemente, replay, lacunas e seleção vazia 404; corpo/configuração/dados inválidos e excesso de concursos 400; JSON malformado 400; GET 405 |

Erros de parsing/método possuem detail; validação de serializer usa erros por campo; erros de domínio usam detail. O 404 legado de latest mantém error. Health é uma função Django sem restrição explícita de método: o contrato de 405 acima refere-se às views DRF, não a health. Não se alterou esse comportamento legado.

## Integração, limites e ausência de vazamento

- `test_generated_tickets_flow_into_fixed_backtest`: 100 jogos com seed mínima de 64 bits, replay JSON idêntico, ausência de SQL na geração, 300 comparações em três concursos, gaps=2, hits e média conferidos por interseções independentes. Conteúdo de Contest preservado; nenhum SyncExecution criado.
- `test_http_future_mutation_and_prefix_invariance`: repetição idêntica; prefixo avaliado isoladamente igual ao prefixo da faixa maior; alteração de todas as dezenas alvo e adição de concurso posterior não modificam jogos selecionados. Complementa o teste puro `test_baseline_cannot_see_target_or_future`.
- O gerador rolling recebe apenas quantidade e RNG; não recebe resultados. Não existe estratégia aprendida neste MVP, portanto não há treinamento histórico a validar. Jogos fixos externos podem ter viés retrospectivo do usuário.
- Banco vazio: resultados/latest, estatísticas e backtest retornam 404 nos testes existentes; gerador funciona sem acesso ao banco. Histórico incompleto seleciona somente registros reais, não preenche lacunas, informa sample_size e missing_count.
- Testes existentes cobrem limites inválidos, constraints inviáveis, máximo de tentativas, RNG global preservado, 201 concursos rejeitados em uma consulta, importação com mocks e retomada de sync após falha.

## Performance e consultas

`test_maximum_http_workload_and_query_bounds` cria 1001 concursos fictícios no banco isolado, consulta estatísticas de 1000 e avalia 200 concursos × 100 jogos. Verifica duas consultas totais: LIMIT 1000 e LIMIT 201. A execução focada mediu 0.093s para as duas requisições, incluindo serialização; JSON do backtest com 936446 bytes. Na suíte final, o teste completo levou 0.14s. São observações locais, não SLA nem benchmark de concorrência.

Latest e detail: uma consulta cada; estatísticas com cutoff: uma; backtest fixed: uma; geração: zero. Índice único em number confirmado por introspecção. Não se observou N+1 nos fluxos testados. Pontos conhecidos: resposta de backtest próxima de 1 MB no teto, recomputação da viabilidade combinatória em cada chamada do gerador e cálculo duplicado de hits no rolling (resultado e baseline iguais). Todos permanecem limitados; não há evidência que justifique otimização funcional nesta tarefa. Não foram feitos testes de carga, memória ou concorrência.

## Defeitos e consistência documental

Nenhum defeito funcional foi reproduzido nos cenários executados; não houve correção especulativa de implementação. Foram corrigidas ambiguidades documentais:

1. P09 anteriormente significava importação histórica opcional: o plano passa a usar P09 para esta validação e OP01 para importação ainda pendente/não autorizada.
2. SPEC-08 ainda apresentava health abreviado e decisões HTTP em aberto: foi registrada a decisão implementada de health completo, vazio=404, erros legados e política pública. README esclarece o alcance do 405.

README e SPEC-05/06/07 correspondem aos limites, defaults, schemas, seed local e modos efetivamente testados. A marcação histórica Proposed/New feature em algumas specs é contexto de elaboração, não evidência de status da entrega; o checklist executado está no plano. Nenhuma interface pública foi modificada.

## Aceitação SPEC-11

| Critério | Resultado/evidência |
| --- | --- |
| Django e endpoints preservados | PASS: check, testes originais de API e integração JSON |
| Suíte original e cobertura adicional | PASS: baseline 104; final 115 |
| Admin inspecionável e imutável | PASS: test_admin, incluído na suíte completa |
| Sync e preservação após falhas | PASS: test_sync_history e test_sync_regressions; rede mockada |
| Estatísticas exatas e sem Caixa | PASS: test_statistics e integração HTTP |
| Gerador limitado e reproduzível | PASS: test_game_generator, test_feature_api e fluxo integrado |
| Backtest exato, limitado, sem influência futura | PASS: test_backtesting e testes HTTP novos |
| Contratos e erros | PASS: matriz de endpoints acima |
| Gates | PASS: Ruff, format, Django e pytest |
| Documentação | PASS: README, specs e decisões revisados |
| Revisão de alterações e escopo | PASS: somente testes/documentação; migrations preservadas, sem import/deploy |

## Limitações e decisão

READY se sustenta na combinação de testes HTTP com PostgreSQL real isolado, integração entre operações, inspeção de migrations, exatidão de métricas, limites/consultas e testes contra influência de resultados futuros; não apenas em testes unitários.

Não executados: Caixa ao vivo, importação real, setup limpo de dependências, servidor TCP/proxy, deployment e testes de carga. Configuração permanece de desenvolvimento. Limitações anteriores permanecem: corrida entre importadores, SIGKILL pode deixar execução running, perda do banco pode impedir logging, filtros raros podem esgotar tentativas. Não se verificou integridade de cada resultado histórico no banco de desenvolvimento. Nenhuma dessas verificações foi apresentada como executada ou necessária para liberação em produção. Nenhuma previsão ou garantia de ganho é inferida do backtest.

Revisão final: `git diff --check` passou (exit 0); arquivos novos também foram lidos diretamente, pois não aparecem no diff de arquivos rastreados. Alterações limitadas aos cinco arquivos listados no plano.
