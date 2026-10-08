# Rule: Missing Number Repetition

**Rule ID:** `missing-number-repetition`

## Definition

`missing-number-repetition` measures how many numbers that were missing in one contest remain missing in the next contest.

Since each contest draws 15 numbers from 25, exactly 10 numbers are missing from each contest.

## Example

```text
Contest X missing:
02, 04, 07, 09, 12, 16, 18, 20, 23, 25

Contest Y missing:
01, 04, 07, 10, 12, 15, 18, 20, 22, 25
```

Repeated missing numbers:

```text
04, 07, 12, 18, 20, 25
```

Result:

```text
Repeated missing numbers: 6
New missing numbers: 4
```

## Rules

* Compare each contest with the immediately previous contest.
* A repeated missing number is absent from both contests.
* Each contest always has exactly 10 missing numbers.
* Historical analysis must track how often each repetition count occurs.

## Expected Output

```json
{
  "rule": "missing-number-repetition",
  "repeated_missing": 6,
  "new_missing": 4
}
```

## Historical Analysis

Calculate:

* Average repeated missing numbers
* Minimum observed
* Maximum observed
* Frequency of each repetition count
* Percentage of contests for each count

