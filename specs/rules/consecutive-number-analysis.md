# Rule: Consecutive Number Analysis

**Rule ID:** `consecutive-number-analysis`

## Definition

`consecutive-number-analysis` identifies consecutive number sequences within a contest and measures the longest consecutive sequence.

## Single Contest Analysis

Example:

```text
01, 02, 03, 05, 06, 09, 10, 11, 12, 15, 18, 20, 21, 23, 25
```

Detected sequences:

```text
01–03 → 3 consecutive numbers
05–06 → 2 consecutive numbers
09–12 → 4 consecutive numbers
20–21 → 2 consecutive numbers
```

Result:

```text
Longest sequence: 4
```

## Rules

* A sequence requires at least 2 consecutive numbers.
* Each sequence must be detected independently.
* The longest sequence must be recorded.
* A contest may contain multiple sequences.
* Isolated numbers are not considered sequences.

## Expected Output

```json
{
  "rule": "consecutive-number-analysis",
  "longest_sequence": 4,
  "sequences": [
    [1, 2, 3],
    [5, 6],
    [9, 10, 11, 12],
    [20, 21]
  ]
}
```

## Historical Analysis

For multiple contests, calculate:

* Average longest sequence
* Minimum longest sequence
* Maximum longest sequence ever observed
* Frequency of each longest-sequence length
* Percentage of contests for each length

Example:

```text
Longest sequence of 3 → 120 contests
Longest sequence of 4 → 540 contests
Longest sequence of 5 → 890 contests
Longest sequence of 6 → 610 contests
Longest sequence of 7 → 180 contests
Longest sequence of 8 → 35 contests
```

## Historical Output

```json
{
  "rule": "consecutive-number-analysis",
  "contests_analyzed": 2375,
  "average_longest_sequence": 4.91,
  "minimum": 2,
  "maximum": 8,
  "distribution": {
    "3": 120,
    "4": 540,
    "5": 890,
    "6": 610,
    "7": 180,
    "8": 35
  }
}
```

