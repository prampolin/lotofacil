# Codex execution prompt — Lotofácil MVP

You are the lead engineer executing an SDD implementation sprint **in this existing repository**. `AGENTS.md`, `plan.md` and `specs/00...11` are your source of product requirements, but the actual repository determines what is already implemented. Do **not** scaffold a replacement application.

## Start
1. Inspect repo root, git status, installed dependencies, Django apps, models, migrations, management commands, URLs, tests and README.
2. Read **all** specs and `AGENTS.md`/`plan.md` before coding. Resolve inconsistent contracts conservatively and record decisions in `plan.md`.
3. Run baseline `ruff check .`, `ruff format --check .`, `python manage.py check`, `python -m pytest -q`; record actual outcomes. If tooling/dependencies/DB unavailable, state precisely what you could not execute and continue on nonblocked tasks; do not invent results.

## Execute
Implement tasks P02–P08 in `plan.md` in dependency order, with tests. Prioritize: admin and stable sync -> pure statistics -> seeded generator -> bounded, leakage-safe backtests -> API integration -> docs. Keep each layer small, comprehensible and aligned to its spec. Preserve backwards compatibility and already passing tests. Update checklist as each step is independently verified.

The timebox is an **aggressive MVP target**, not permission to skip validation. Prefer a smaller finished slice to numerous untested stubs. Work autonomously on reversible code changes without asking for routine confirmations.

## Non-negotiable
Never reset/drop production/dev database, delete Docker volumes, rewrite applied migrations, mass-import contests, execute deploy, commit secrets, or claim winning-number prediction. Avoid new packages unless needed and justified. Mock Caixa network in tests. For backtesting, ensure a target draw never influences generation of its own ticket.

## Finish
Rerun all quality gates and report: files changed; behavior and API endpoints implemented; sample curl calls; tests passed/failed/skipped; migrations; gaps and limitations; `plan.md` updated. If anything remains incomplete, mark it explicitly TODO/BLOCKED; do not say MVP is done until SPEC-11 is satisfied.
