# Rule: Gap Distribution

**Rule ID:** `gap-distribution`

## Definition

`gap-distribution` analyzes the gaps of missing numbers between selected numbers in a contest.

A gap is the number of consecutive unselected numbers between two selected numbers.

## Gap Types

```text
Gap 0 → consecutive numbers
Gap 1 → one missing number
Gap 2 → two missing numbers
Gap 3 → three missing numbers
Gap 4 → four missing numbers
...
```

## Example

Selected numbers:

```text
01, 02, 05, 09, 10, 14
```

Detected gaps:

```text
02 → 05 = gap 2
05 → 09 = gap 3
10 → 14 = gap 3
```

Result:

```text
gap 2 → 1 occurrence
gap 3 → 2 occurrences
```

## Rules

* Only gaps between two selected numbers are counted.
* Missing numbers before the first selected number are ignored.
* Missing numbers after the last selected number are ignored.
* A gap of `0` represents consecutive selected numbers.
* `triple-jump` is equivalent to detecting at least one gap of size `3`.

## Expected Output

```json
{
  "rule": "gap-distribution",
  "gaps": {
    "0": 2,
    "1": 0,
    "2": 1,
    "3": 2
  },
  "largest_gap": 3
}
```

## Historical Analysis

For multiple contests, calculate:

* Frequency of each gap size
* Average number of gaps per contest
* Largest gap observed
* Frequency of contests containing each gap size

