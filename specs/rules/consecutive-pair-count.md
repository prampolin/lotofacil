# Rule: Consecutive Pair Count

**Rule ID:** `consecutive-pair-count`

## Definition

`consecutive-pair-count` measures how many adjacent number pairs exist within a contest.

A consecutive pair occurs when two selected numbers differ by exactly `1`.

## Example

Selected numbers:

```text
01, 02, 03, 07, 08, 11, 15
```

Consecutive pairs:

```text
01-02
02-03
07-08
```

Result:

```text
Consecutive pairs: 3
```

## Rules

* Each adjacent pair counts independently.
* A sequence of 3 numbers creates 2 consecutive pairs.
* A sequence of 4 numbers creates 3 consecutive pairs.
* Isolated numbers do not create pairs.

## Historical Analysis

For multiple contests, calculate:

* Average consecutive-pair count
* Minimum observed count
* Maximum observed count
* Frequency of each count
* Percentage of contests for each count

## Expected Output

```json
{
  "rule": "consecutive-pair-count",
  "count": 3
}
```

