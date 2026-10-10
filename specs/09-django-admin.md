# SPEC-09 — Django Admin
**Priority:** P1 | **Status:** New or incomplete; verify

## Responsibilities
Make existing result data and execution status inspectable by a superuser. Do not build bespoke frontend.

## ContestAdmin
List: number, draw_date, optionally created_at; search by number (use numeric field semantics), filter by draw_date, order newest number first. Show numbers cleanly in detail. Prefer read-only for imported draw content or protect edits with existing validation if writing permitted.

## SyncExecutionAdmin
List: id, status, start_contest, end_contest, processed, started_at, finished_at; filter status/start time; search id; read-only audit trail; disable direct creation/deletion or manual status mutation unless documented need.

## Security
Existing Django superuser access only. Never expose admin endpoints publicly without authentication. Keep admin registration idempotent.

## Tests
Both models registered, expected list display, unsafe field edits blocked if configured.

## Acceptance
Admin can inspect contestants and runs; audit history cannot be casually rewritten from admin; no new migrations needed unless justified.
