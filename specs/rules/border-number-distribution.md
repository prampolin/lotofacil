# Rule: Border Number Distribution

**Rule ID:** `border-number-distribution`

## Definition

`border-number-distribution` measures how many drawn numbers belong to the predefined border set.

## Border Numbers

```text
01, 02, 03, 04, 05,
06, 10,
11, 15,
16, 20,
21, 22, 23, 24, 25
```

There are **16 border numbers** in total.

## Scope

The rule must support:

* A single contest
* A range of contests
* The last `N` contests
* One or more cycles

## Single Contest

Example:

```text
Border numbers drawn: 10
Non-border numbers drawn: 5
```

## Historical Analysis

For multiple contests, calculate:

* Average border-number count
* Minimum observed count
* Maximum observed count
* Frequency of each border-count value
* Percentage of contests for each count

Example:

```text
8 border numbers  → 12 contests
9 border numbers  → 35 contests
10 border numbers → 48 contests
11 border numbers → 27 contests
12 border numbers → 8 contests
```

The historical average represents the estimated border-number count.

## Expected Output

```json
{
  "rule": "border-number-distribution",
  "contests_analyzed": 130,
  "average_border_count": 9.87,
  "minimum": 7,
  "maximum": 12,
  "distribution": {
    "8": 12,
    "9": 35,
    "10": 48,
    "11": 27,
    "12": 8
  }
}
```

