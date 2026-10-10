# SPEC-06 — Game generator
**Priority:** P0 | **Status:** New feature

## Input
`quantity`: integer default=1, range 1..100; `seed`: optional integer (32/64-bit range may be selected but document it); `constraints` optional object with `odd_min`, `odd_max`, `sum_min`, `sum_max`; unsupported keys must fail validation, not be ignored. Decide named fields once in serializers and document.

## Invariants
Every result has 15 distinct integers in [1,25], sorted ascending. No duplicates across one response. Same complete input + seed -> same output in a fixed implementation version. Never mutate module-global RNG state.

## Algorithm
Uniform baseline: `random.Random(seed).sample(range(1,26), 15)`; sorting before output. For optional constraints, rejection-sample with bounded attempts (e.g. max 10,000 total or 1,000 per required game), and fail deterministically with a clear domain error if insufficient distinct tickets satisfy constraints. Validate obvious impossible combinations immediately (`odd_min > odd_max`, sum outside possible [120,270], etc.). Do not promise unconstrained uniform sampling under filters without proving it.

## Outputs
`games` as list of sorted integer arrays; `quantity`, `seed` (or null if not supplied), applied constraints, and attempts if useful. Do not label as predicted/optimal.

## HTTP
POST `/api/v1/games/generate/`; 200 valid, 400 malformed constraints or impossible request; no database write.

## Tests
Values, uniqueness, sort order, seeded reproducibility, no duplicate games, parity/sum constraints, impossible constraint, malformed input, quantity boundaries and attempts exhausted.

## Acceptance
All invariants pass in tests; bounded runtime; no historical dependence required for baseline.
