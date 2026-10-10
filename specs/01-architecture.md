# SPEC-01 — Architecture
**Priority:** P0 | **Status:** Proposed

## Principle
Preserve existing Django app(s), settings and commands. Favor small, pure domain modules inside the current `results` app unless audit reveals a compelling structure already present.

## Recommended logical layers
1. Models: persistence (`Contest`, `SyncExecution`).
2. Integration: Caixa HTTP adapter and data normalization (`requests`, timeout, error classification).
3. Domain services: `statistics`, `game_generator`, `backtesting` as pure Python calculations or explicit QuerySet readers; no DRF request objects.
4. Application: command handlers and API views coordinate services.
5. Interface: serializers validate inputs; response schema is documented.

## Invariants
`Contest.number` unique positive; `draw_date` valid; `numbers` exactly 15 distinct integers from 1 through 25 in ascending order when saved or returned. Existing model validation must not be weakened.

## Decisions
- Keep `/api/v1/` as the single versioned prefix.
- Preserve current result URLs.
- Use integer seed with local `random.Random(seed)`, never global RNG mutation.
- Use consistent window semantics documented in SPEC-05.
- Historical backtests compute features from strictly earlier draws.
- Prefer no extra runtime dependencies for MVP.

## Acceptance
No circular imports, no external HTTP in core algorithms, old routes unaffected, command/UI tests pass.
