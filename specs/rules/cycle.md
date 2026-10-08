# Rule: Cycle

**Rule ID:** `cycle`

## Definition

A `cycle` is a sequence of consecutive contests required for all **25 numbers** to appear at least once.

A cycle starts with a contest and remains open while there are still numbers that have not appeared.

The cycle ends on the first contest where the accumulated drawn numbers contain all numbers from `01` to `25`.

The next contest starts a new cycle.

## Example

```text
Contest 100 → 15 unique numbers seen
Contest 101 → 20 unique numbers seen
Contest 102 → 23 unique numbers seen
Contest 103 → 25 unique numbers seen
```

Result:

```text
Cycle #1
Start: Contest 100
End: Contest 103
Length: 4 contests
Status: closed
```

Contest `104` starts the next cycle.

## Rules

* Each number only needs to appear once to be considered seen.
* Repeated appearances do not affect cycle progress.
* A cycle remains open until all 25 numbers have appeared.
* The contest that completes the 25-number set belongs to the current cycle.
* The next cycle starts only in the following contest.

## Current Cycle State

Example:

```json
{
  "rule": "cycle",
  "cycle": 38,
  "status": "open",
  "start_contest": 3201,
  "contests": 4,
  "seen_count": 23,
  "missing": [7, 19]
}
```

## Closed Cycle

```json
{
  "rule": "cycle",
  "cycle": 38,
  "status": "closed",
  "start_contest": 3201,
  "end_contest": 3205,
  "length": 5
}
```

