# SPEC-08 — REST API
**Priority:** P0 | **Status:** Existing endpoints + proposed additions

## Existing routes: preserve
- GET `/api/v1/health/` -> 200 `{ "status": "ok" }` (verify existing shape)
- GET `/api/v1/results/latest/` -> most recent by contest number
- GET `/api/v1/results/<number>/` -> specific contest or 404
Never break current serializer keys `number`, `draw_date`, `numbers`.

## Proposed routes
- GET `/api/v1/statistics/?window=100&as_of_contest=123` -> 200 statistics per SPEC-05
- POST `/api/v1/games/generate/` -> 200 games per SPEC-06
- POST `/api/v1/backtests/` -> 200 backtest per SPEC-07

## HTTP contracts
JSON request/response. Serializer validates types, ranges and unsupported constraint keys; errors returned as structured 400; empty data 404 or 400/422 **choose and document consistently**. Do not expose tracebacks, database credentials or arbitrary exceptions in HTTP.

## Example generation request
```json
{"quantity": 2, "seed": 42, "constraints": {"odd_min": 6, "odd_max": 9, "sum_min": 170, "sum_max": 230}}
```

## Example backtest request
```json
{"start_contest": 220, "end_contest": 230, "mode": "fixed_games", "games": [[1,2,3,4,5,6,7,8,9,10,11,12,13,14,15]]}
```

## Compatibility
Keep router/base prefix and DRF permission behavior as in repository; explicitly document current access policy, do not invent an authentication system. Use service functions in views.

## API tests
200, 400 invalid query/body, 404 missing result/empty selected data, deterministic generation, database selection boundaries, stable response schema.

## Acceptance
Routes reachable, documented with curl examples and tested without external requests.

## Contrato confirmado por P09 (2026-10-10)

Health preserva `{"status":"ok","service":"lotofacil-api","version":"1.0.0"}` e sua view Django não restringe métodos. As views DRF rejeitam métodos não implementados com 405. Seleção vazia/concurso ausente retorna 404; entrada inválida retorna 400. Erros de domínio usam `detail`; serializers retornam erros por campo; latest vazio preserva o legado `error`. API pública, admin autenticado. Schemas completos, defaults e limites estão no README; evidências HTTP/PostgreSQL em `docs/mvp-validation.md`.


## Proteção de payload P11

Sem alterar contratos de sucesso ou acesso público, corpos maiores que 64 KiB em `/api/v1/` são rejeitados com 413 e JSON `detail` antes de parsing/serviços. Content-Length inválido retorna 400. Limite de tamanho não é rate limiting; controle de tráfego fica pendente na infraestrutura.
