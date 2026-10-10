# SPEC-07 — Historical backtesting
**Priority:** P0 | **Status:** New feature

## Scope
Historical evaluation of explicit ticket(s) and a seeded baseline, plus **optional** historical strategy that chooses tickets from prior draws only. No winnings/prize estimate in MVP.

## Input and bounds
`start_contest`, `end_contest` inclusive, both positive and start<=end; cap evaluated existing draws (e.g. <=200) to protect compute; `games` optional list of validated 15-number tickets (max 100), otherwise `quantity` and `seed` to generate baseline games. Specify mode `fixed_games` or `rolling_baseline`; no ambiguous silent switch. If implementing history-informed heuristic, require documented training window and minimum prior draws.

## Metrics
For every evaluated historical contest and ticket: `hits = len(set(game) & set(draw.numbers))`, integer [5,15] for valid Lotofácil combinations; report 0..15 in distribution schema (0..4 naturally zero). Aggregate per-hit counts, total comparisons, per-draw breakdown (bounded), average hits = total hits / comparisons, and denominator/sample size. Missing contest numbers are omitted and counted explicitly; do not invent results.

## No look-ahead
When generating a ticket for target contest K using historical statistics, supply only contests with number **strictly less** than K. Do not compute features over the entire evaluation range first. Seed handling must be documented and reproducible (single local RNG or deterministic per-target seed).

## Fair comparison
Use the same evaluation draws and ticket count for strategy and random baseline. Any claimed improvement must include sample size and is descriptive; no claims of statistical significance or predictive edge without proper analysis.

## API
POST `/api/v1/backtests/`; return mode, effective range, draw count, game count, comparisons, distribution, avg_hits and config/baseline summary. Enforce compute caps in serializer/service; error on empty dataset.

## Tests
Exact fixture hit counts, range inclusivity, gaps, invalid games, reproducibility, upper bounds, zero draws, strict-prior-data test designed to catch future leakage.

## Acceptance
Reproduces fixture results; baseline under same conditions; no HTTP; no leakage.
