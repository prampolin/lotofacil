# Lotofácil — API REST MVP

Backend existente Django + DRF, PostgreSQL 17. Estatísticas descritivas, geração de combinações e avaliação histórica. Não prevê resultados nem garante ganhos. Sem frontend, pagamentos ou deploy neste escopo.

## Ambiente local

Versões verificadas: Python 3.14.7, Django 6.1.2, DRF 3.18.3. Dependências diretas reproduzíveis em `backend/requirements.txt`.

```sh
cd backend
python3.14 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
# Em ambiente novo: copie .env.example para .env e preencha os segredos.
# Não sobrescreva um .env existente.
set -a
source .env
set +a
docker compose up -d postgres
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Os comandos acima são instruções de setup, não foram executados neste sprint. Se `.venv` e PostgreSQL já existem, reutilize-os. O compose mantém `postgres_data`; não remova volumes. Configuração por ambiente: `DJANGO_SECRET_KEY` obrigatório, `POSTGRES_PASSWORD` externo e `DEBUG=false` por padrão. O `.env` local é privado/ignorado e precisa ser carregado no shell; não é lido automaticamente pelo Django. Para debug local, defina `DJANGO_DEBUG=true`. Gere uma chave privada com `python -c "import secrets; print(secrets.token_urlsafe(64))"`. Produção usa `--settings=config.production` e exige hosts explícitos, chave forte e senha do banco; veja `docs/security-performance.md`. O banco SQLite vazio não é utilizado. Não há migrações novas.

Admin em `http://127.0.0.1:8000/admin/`: acesso autenticado Django; superusuário pode consultar concursos e execuções. Inclusão, edição e exclusão ficam bloqueadas no admin. Busca por número/id, filtros por data/status. Nenhum usuário foi criado automaticamente.

## Endpoints

Política DRF existente preservada: API pública, sem exigir autenticação. Admin requer login. Novas operações não gravam concursos ou jogos e não consultam Caixa. Requisições POST usam JSON; campos desconhecidos são rejeitados, inclusive dentro de constraints. Booleanos, strings e floats não substituem inteiros JSON.

| Método | Caminho | Resultado |
| --- | --- | --- |
| GET | `/api/v1/health/` | `{"status":"ok","service":"lotofacil-api","version":"1.0.0"}` |
| GET | `/api/v1/results/latest/` | Maior número de concurso armazenado |
| GET | `/api/v1/results/<number>/` | Concurso específico |
| GET | `/api/v1/statistics/` | Estatísticas da janela armazenada |
| POST | `/api/v1/games/generate/` | Jogos com seed e filtros opcionais |
| POST | `/api/v1/backtests/` | Comparação histórica e baseline |

Resultados preservam `number`, `draw_date` (ISO) e `numbers`. Sucesso=200; entrada inválida=400; concurso/seleção vazia=404; método incorreto nas views DRF=405 (health preserva a view Django sem restrição de método). Erros novos de domínio: `{"detail":"mensagem"}`; erros de serializer: objeto por campo com listas de mensagens. JSON malformado retorna 400. Não há exposição de exceções arbitrárias pelas novas views.

### Estatísticas

```sh
curl 'http://127.0.0.1:8000/api/v1/statistics/?window=100&as_of_contest=230'
```

`window`: 1..1000, padrão 100; `as_of_contest`: positivo opcional, limite inclusivo. Usa os últimos N concursos **armazenados**, ordenados por número, com uma consulta limitada. Lacunas não criam resultados. Janela menor que N retorna o tamanho real.

Resposta:

- `window`, `as_of_contest` (null se ausente), `sample_size`, `first_contest`, `last_contest`.
- `numbers`: 25 objetos com `number`, `count`, `frequency_pct` (2 casas), `draws_since_last_seen` (null se não observado na amostra).
- `contests`: objetos com `number`, `odd_count`, `even_count`, `sum`, `consecutive_pairs`, `repeated_from_previous` (primeiro=null).
- `aggregates`: `odd_distribution` e `even_distribution` mapeiam contagem para quantidade de concursos; `sum` contém min/max/mean; `mean_consecutive_pairs` e `mean_repetitions`, esta última null para uma única observação. Médias com 2 casas; chaves numéricas de distribuições são strings no JSON. Categorias de paridade não observadas são omitidas.

Dezenas armazenadas inválidas retornam 400, sem alteração dos dados. Frequência histórica não é estimativa da chance de uma dezena no próximo sorteio.

### Geração

```sh
curl -X POST http://127.0.0.1:8000/api/v1/games/generate/ \
  -H 'Content-Type: application/json' \
  -d '{"quantity":2,"seed":42,"constraints":{"odd_min":6,"odd_max":9,"sum_min":170,"sum_max":230}}'
```

`quantity`: 1..100, padrão 1. `seed`: inteiro de -2^63 a 2^63-1, opcional/null. A mesma entrada completa e seed reproduz a saída nesta versão da implementação; sem seed não há garantia de replay. Usa RNG local sem modificar o global.

Cada jogo contém 15 inteiros distintos de 1..25 em ordem crescente; não há jogos repetidos na resposta. `constraints` é opcional; defaults efetivos: odd_min=3, odd_max=13, sum_min=120, sum_max=270. Paridade aceita limites 0..15, mas combinações inviáveis são rejeitadas; soma aceita 120..270. Valida viabilidade combinada de paridade/soma e relações mínimo/máximo. Até 10000 tentativas totais de amostragem por rejeição; filtros raros podem esgotar o limite mesmo sendo matematicamente viáveis (400, sem saída parcial).

Resposta: `games` (arrays), `quantity`, `seed`, `constraints` (valores efetivos) e `attempts`. Não há classificação de jogos como melhores ou preditivos.

### Avaliação histórica

```sh
curl -X POST http://127.0.0.1:8000/api/v1/backtests/ \
  -H 'Content-Type: application/json' \
  -d '{"start_contest":220,"end_contest":230,"mode":"fixed_games","seed":42,"games":[[1,2,3,4,5,6,7,8,9,10,11,12,13,14,15]]}'

curl -X POST http://127.0.0.1:8000/api/v1/backtests/ \
  -H 'Content-Type: application/json' \
  -d '{"start_contest":220,"end_contest":230,"mode":"rolling_baseline","quantity":2,"seed":42}'
```

`mode` é obrigatório:

- `fixed_games`: requer 1..100 jogos válidos e distintos, repetidos em cada concurso avaliado. Rejeita quantity. Baseline aleatório usa os mesmos concursos e a mesma quantidade; seed controla esse baseline.
- `rolling_baseline`: rejeita games, aceita quantity 1..100 (padrão 1). Gera jogos novos em cada concurso com um único RNG local percorrendo os concursos armazenados em ordem crescente. Gerar o jogo não recebe resultados históricos ou futuros. Alterar a faixa inicial ou preencher lacunas muda a sequência de RNG.

Faixa inclusiva, positiva, início <= fim (números até 2147483647); no máximo 200 concursos armazenados, 100 jogos por concurso e 20000 comparações por grupo. Consulta carrega até 201 linhas para detectar excesso. Lacunas são omitidas e contadas. Baseline limita tentativas a 10000 por concurso. Não há heurística aprendida neste MVP; se futuramente adicionada, deverá receber somente concursos anteriores ao alvo. A escolha externa de jogos fixos pelo usuário pode conter viés retrospectivo.

Resposta: `mode`, `requested_range`/`effective_range` (`start`/`end`), `draw_count`, `missing_count`, `game_count` (por concurso), `comparisons`, `distribution` (todas as chaves 0..15), `avg_hits` (4 casas). `baseline` contém distribution/avg_hits/comparisons. `config` contém seed, seed_policy e training_window=null. `contests` contém number, games, hits e baseline_hits. Acertos válidos ficam em 5..15; categorias 0..4 ficam zeradas. No modo rolling, métricas e baseline são idênticos. Não estima prêmios ou significância estatística.

## Importação e sincronização

Comandos existentes preservados: `import_contests --number INT`; `import_history --start INT --end INT --delay FLOAT`; `sync_history --start INT --batch-size INT --limit INT --delay FLOAT [--dry-run]`. Nenhum foi executado contra a Caixa neste sprint.

A importação direta atualiza concurso existente; histórico/sync pulam números já armazenados. Intervalo/limite máximo 100; delay finito >=1 segundo. Timeout HTTP=20s; import_history repete somente erros transitórios (429/5xx/timeout/conexão), até 3 tentativas, esperas de 2 e 4 segundos. 400/404/JSON/schema inválido são permanentes. Consulta inicial do sync à Caixa falha imediatamente se indisponível, sem criar execução.

Dry-run consulta o último número remoto e informa contagens sem gravar. Sync ordena ausentes, limita seleção e grava processed após cada importação bem-sucedida. Falha preserva progresso e causa; próxima execução seleciona ausentes. processed significa importações retornadas com sucesso, não necessariamente linhas novas em cenário concorrente. Se logging também falhar, causa original é relançada e falha adicional vai para stderr. SIGKILL ou perda do banco pode deixar running: revisar manualmente, não há recuperação automática. Não executar importadores concorrentes; corrida pode gerar erro de unicidade, sem duplicação por causa da constraint. Não há scheduler/queue ou logs por concurso.

Importação histórica em massa permanece pendente e deve ser autorizada e executada manualmente em lotes após revisão. Não apagar dados para resolver conflitos.

## Verificação

Na pasta backend, com venv ativo, variáveis de `.env` exportadas e PostgreSQL disponível:

```sh
ruff check .
ruff format --check .
python manage.py check
python manage.py makemigrations --check --dry-run
python -m pytest -q
```

pytest-django cria banco isolado `test_lotofacil`; não usa tabelas do banco de desenvolvimento nos testes. Chamadas requests externas são bloqueadas por fixture autouse; testes Caixa usam mocks. A migração preexistente 0002 está excluída somente do formatador para cumprir a regra de não reescrever migrações aplicadas; permanece no lint e nas migrações de teste.

Evidências por etapa e resultado final estão em `plan.md`. Critérios, decisões e limitações adicionais: `specs/`. Histórico e arquivos JSON/XLSX prévios foram preservados. Não houve deploy, importação real ou migração no banco de desenvolvimento.

Validação integrada P09: [relatório e evidências](docs/mvp-validation.md).


## Segurança e estabilidade (P11)

API pública preservada; CORS não habilitado. Payloads em `/api/v1/` têm limite de 64 KiB (413 JSON acima do limite). Limites de cálculo continuam 1000 concursos em estatísticas, 100 jogos, 10000 tentativas e 200 concursos por backtest. Não há rate limiting distribuído; configurar na borda antes de exposição pública.

Os três comandos de importação agora compartilham advisory lock PostgreSQL de sessão: somente um importador por banco, inclusive entre processos; concorrentes falham antes da rede. Requer conexão direta ou pooling de sessão (não pooling de transação). Ctrl-C registra falha no sync quando já existe log; SIGKILL pode deixar running. Antes de retomar, confirmar término do processo e liberar qualquer autorização necessária; o comando consulta os concursos ausentes. Logs antigos não são modificados automaticamente.

P11 não executou importações ou deploy e preservou os 266 concursos e 2 logs. Histórico Git ainda contém credenciais antigas: a remoção no código atual não substitui rotação coordenada nem limpeza do histórico. Relatório, medições locais e pendências operacionais: [docs/security-performance.md](docs/security-performance.md).

### Espera solicitada pela Caixa

`import_history` respeita `Retry-After` em erros HTTP transitórios (429/5xx),
aceitando segundos inteiros ou data HTTP. A pausa considera o maior valor entre
esse cabeçalho, `--delay` e o backoff existente; o limite continua em três
tentativas. Cabeçalho inválido usa o backoff habitual. Espera solicitada acima
de 300 segundos interrompe a execução para retomada posterior, sem antecipar a
requisição. Validado com PostgreSQL no banco isolado do pytest-django (P12).
