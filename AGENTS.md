# AGENTS — Lotofácil

## Mission
Deliver a verifiable Django REST MVP using the specifications in `specs/` and the execution checklist in `plan.md`.

## Mandatory workflow
1. Determine repository root (`git rev-parse --show-toplevel`); inspect the real codebase before changing files. If these documents reside in a subfolder, use that folder as the specification root.
2. Read `plan.md`, `specs/00-project-overview.md`, the relevant feature spec, and `specs/11-acceptance-criteria.md` before each task.
3. Mark task `IN_PROGRESS`; implement a small, coherent change; run appropriate focused tests; update status with evidence. Only mark `DONE` after verification.
4. Existing behavior and migrations are the source of truth. Resolve discrepancies with specs by documenting a decision in `plan.md` before modifying a public contract.
5. Never drop/truncate DB tables, delete Docker volumes, rewrite applied migrations, mass-import contests automatically, commit secrets, or deploy without explicit authorization.
6. Preserve `Contest`, `SyncExecution`, existing CLI arguments, endpoint paths, and all passing tests. Create additive migrations only if genuinely needed.
7. Keep pure domain logic independent of views. No external HTTP in statistics, generation, or backtesting.
8. Mock Caixa network calls in tests. Run tests against pytest-django's test database, never the development/production database.
9. Prevent future data leakage in rolling historical evaluations. No claim of lottery prediction or guaranteed success.
10. Stop and report blockers truthfully. Never claim a command or test passed if it was not executed.

## Quality gates
- `ruff check .`
- `ruff format --check .`
- `python manage.py check`
- `python -m pytest -q`
- Record actual outputs and any unmet checks in `plan.md`.

## Scope guard
MVP = admin, robust sync, statistics, generator, historical evaluation, API, tests, docs. No frontend, payments, auth system redesign, AI prediction, or deployment in this sprint.
