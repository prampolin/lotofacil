# SPEC-11 — Release acceptance
**Priority:** P0 | **Status:** Proposed

## MVP must pass
- [ ] Existing Django app boots; health and old result endpoints retain behavior.
- [ ] Original tests pass and added tests cover all new features.
- [ ] Admin can inspect contests and immutable/auditable sync records.
- [ ] Import resumes without damaging existing contest rows or incorrectly marking failures completed.
- [ ] Statistics on known fixture match hand-computed counts and never query Caixa.
- [ ] Generated games meet 15-of-25 rules, are unique per batch, respect filters and deterministic seed.
- [ ] Backtest reproduces exact fixture hits; bounded; uses only pre-target data for learned strategies.
- [ ] New API routes respond with documented JSON; validate malformed requests with 4xx.
- [ ] `ruff check .`, `ruff format --check .`, `python manage.py check`, `python -m pytest -q` pass.
- [ ] README contains setup, docker compose, venv, migrate, runserver, endpoints + curl, tests, limitations.
- [ ] Git diff reviewed; no secrets, deleted DB volumes, destructive migrations, unsolicited deployment/import.

## Delivery report
For every item report PASS / FAIL / NOT RUN with precise evidence. Report changed files, commands and exit status, known issues, deviations from specifications, and the next priority.

## Explicit limitation
A historical simulation, even if reproducible, does not establish predictive power for future lottery draws. Avoid marketing promises.
