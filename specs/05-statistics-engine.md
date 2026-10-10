# SPEC-05 — Statistics engine
**Priority:** P0 | **Status:** New feature

## Data selection contract
Sort contests by draw number ascending, not insertion order. `window=N` selects the N **most recent stored contests** (default=100, allowed 1..1000); if fewer are stored, use available and report `sample_size` explicitly. Optional `as_of_contest` selects only `number <= as_of_contest`. For backtesting training data, caller must select contests with `number < target_number` (strict!). Reject empty datasets with clear error/404 or 422/400 per API convention.

## Output rules
For each number 1..25:
- `count`: occurrences in selected draws.
- `frequency_pct`: `count / sample_size * 100`, rounded consistently to 2 decimals.
- `draws_since_last_seen`: count of sampled draws after last appearance, or `null` if never appeared in sample.
For each contest: `odd_count`, `even_count`, `sum`, `consecutive_pairs` (count of adjacent values n,n+1), `repeated_from_previous` (intersection with immediately preceding **selected** contest; first= null).
Aggregates: odd/even distribution, min/max/mean sum, mean consecutive pairs, mean repetitions excluding first; if only one sample, corresponding mean repetitions = null.

## Data correctness
Only persisted historical results. Validate unusual stored JSON defensively rather than silently treating invalid contests as valid. Gaps in contest numbering do not imply fabricated draws. Percentages are descriptive and NOT probability estimates for an individual next draw.

## API hints
GET `/api/v1/statistics/?window=100[&as_of_contest=...]`; document exact JSON in SPEC-08 implementation and README. Avoid heavy per-row queries; one bounded query.

## Tests
Known fixtures with hand-calculated values, zero occurrences, repeated/adjacent values, 1-result window, empty DB, window bounds, `as_of_contest`, determinism.

## Acceptance
Calculation matches fixtures precisely; default bounded; no external HTTP; REST validates all inputs.
