# SPEC-10 — Testing & verification
**Priority:** P0 | **Status:** Existing test suite, extend

## Baseline first
Run and record actual: `python -m pytest -q`, `ruff check .`, `ruff format --check .`, `python manage.py check`, `python manage.py makemigrations --check --dry-run`. In the previous interaction, 16 tests were confirmed passing; 2 new sync-log tests were drafted but passing status is not yet independently confirmed. Never assume 18 pass.

## Test taxonomy
- Domain unit: pure functions with hand-computable fixtures.
- Integration: Django ORM with isolated pytest-django test database.
- HTTP: DRF test client for routes, JSON schema and validation.
- Commands: mock `requests.get`, mock sleeps and nested commands selectively; also test model state.
- Regression: all original tests preserved.

## Required edge cases
- Invalid draw, duplicate/import idempotence, error classification, retry cap.
- Sync completed, failed after one success, dry-run no DB change, no-op, resume.
- Statistics empty data, `window`, correct denominator, previous-draw overlaps.
- Games random seed, constraints, impossibility, duplicate protection.
- Backtest exact hits, gap, range limit, replay consistency and no look-ahead.

## Test hygiene
Never access live Caixa, run full history import, or use real developer DB during tests. Tests must be repeatable and reasonably fast.

## Acceptance
All verified tests pass, lint/format/checks pass; any skipped/blocked command explicitly logged rather than treated as pass.
