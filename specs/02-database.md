# SPEC-02 — Database & integrity
**Priority:** P0 | **Status:** Existing schema to verify

## Existing models (verify exact implementation)
`Contest`: `number` unique positive integer; `draw_date` date; `numbers` JSON list; `created_at` auto timestamp; ordering by descending contest number. `SyncExecution`: `started_at`, nullable `finished_at`, `status` (`running|completed|failed`), `start_contest`, `end_contest`, `processed`, `error_message`.

## Rules
- Normalize `numbers` ascending, validate length=15, uniqueness and domain=[1,25].
- Imports idempotent: duplicate contest number updates or skips according to existing command's documented behavior.
- Logs are **not** business data source for contest results. No cascade should remove contests when log changes.
- Never replace applied migrations. If necessary, generate additive migration and inspect SQL.
- Never use actual developer DB in pytest; pytest-django must create a separate test database.

## Indexing/scale
Contest `number` unique indexed; inspect ORM queries and indexes before adding new ones. ~thousands of rows does not demand premature optimization.

## Cases
Missing contest, invalid date, repeated/unsorted numbers, duplicate number, database exception while logging, concurrent import race (document if not fixed).

## Acceptance
Validation tests, migration consistency (`makemigrations --check --dry-run`), database records preserved.
