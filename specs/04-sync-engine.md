# SPEC-04 — Incremental synchronization
**Priority:** P0 | **Status:** Implemented core; audit and harden

## Existing CLI contract (preserve)
`python manage.py sync_history --start INT --batch-size INT --limit INT --delay FLOAT [--dry-run]`; documented expected bounds: start>=1, batch_size/limit 1..100, delay>=1 sec. Current logic calculates missing numbers between start and latest contest and processes up to limit in ascending order.

## Behavior
1. Validate CLI input before any mutation.
2. Fetch latest published draw number; query numbers already saved in requested range.
3. `--dry-run` reports selection and changes neither contests nor `SyncExecution`.
4. If none selected, report no-op and do not create `SyncExecution`.
5. On a real run, create `running` record with first/last selected numbers; update `processed` after each successful import; on success set `completed` and `finished_at`; on failure set `failed`, `finished_at`, `error_message`, retain prior progress and re-raise.
6. Re-run selects only remaining numbers (resumable). Do not mark a failed import as completed.

## Clarifications
`processed` counts successfully returned per-contest imports, not necessarily newly added DB rows if concurrent writers are active. If labels say “imported,” ensure semantics match or rename to “processed.” A Python process crash / SIGKILL may leave `running`; document and, if low-risk, add stale-run detection.

## Required tests
Dry run/no-op, skipped existing, limit, ordering, success record, failure on second of three (processed=1), re-run after failure, malformed CLI input, logging failure where appropriate.

## Acceptance
All old sync tests pass; new audit tests pass; no destructive database actions; no silent error swallowing.
