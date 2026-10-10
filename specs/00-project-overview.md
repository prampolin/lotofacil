# SPEC-00 — Product overview
**Priority:** P0 | **Status:** Proposed, audit against code

## Goal
Ship an API-first MVP for inspecting historical Lotofácil draw results, generating valid ticket combinations, and honestly evaluating strategies on historical draws.

## Confirmed context from prior development
Django + DRF, PostgreSQL 17 (Docker), models `Contest` and `SyncExecution`, commands `import_contests`, `import_history`, `sync_history`, versioned result routes, pytest and Ruff. Last reported Caixa contest was 3801, with 241 imported following successful import of 230–232; these are snapshots, not live guarantees. Verify current database and code before assumptions.

## Users and workflows
- Developer/admin imports missing contests, observes progress/errors, inspects stored results.
- API consumer lists statistics for a bounded historical window.
- API consumer generates valid combinations under explicit constraints.
- API consumer runs a bounded historical evaluation with reproducible settings.

## MVP boundaries
IN: Django Admin; safe existing importers; statistics; games; backtests; versioned REST; tests and docs.
OUT: user accounts beyond Django admin, subscriptions, frontend, prediction model, automated mass synchronization, deployment, prize-money estimates, financial guarantees.

## Nonfunctional
Deterministic under explicit seed, bounded CPU/DB work, clear 4xx errors, isolation from external API in calculations, reproducible tests, no look-ahead bias, traceable specs-to-tests.

## Acceptance
All feature specs' hard criteria pass; existing endpoints/tests remain working; `plan.md` contains execution evidence. A strategy's past score is **not** a forecast of future outcomes.
