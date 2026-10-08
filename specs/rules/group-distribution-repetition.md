# Rule: Group Distribution Repetition

**Rule ID:** `group-distribution-repetition`

## Definition

`group-distribution-repetition` analyzes how the 15 drawn numbers are distributed across five fixed groups and whether the same distribution pattern repeats in the next contest.

## Groups

```text
G1: 01–05
G2: 06–10
G3: 11–15
G4: 16–20
G5: 21–25
```

## Distribution Signature

Example:

```text
Contest X → 3, 3, 3, 3, 3
Contest Y → 4, 2, 3, 3, 3
```

The distribution did not repeat.

If:

```text
Contest X → 3, 3, 3, 3, 3
Contest Y → 3, 3, 3, 3, 3
```

the distribution repeated.

## Rules

* Each contest must produce a five-value distribution signature.
* The sum of all values must always equal `15`.
* Consecutive contests must be compared.
* A repetition occurs only when all five distribution values are identical.
* Historical analysis must measure how often each distribution repeats in the immediately following contest.

## Expected Output

```json
{
  "rule": "group-distribution-repetition",
  "previous_distribution": [3, 3, 3, 3, 3],
  "current_distribution": [3, 3, 3, 3, 3],
  "repeated": true
}
```

## Historical Analysis

The rule should also calculate:

```text
Distribution: 3-3-3-3-3
Occurrences: 42
Repeated in next contest: 3
Repetition rate: 7.14%
```

