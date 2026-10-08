# Rule: Contest Number Repetition

**Rule ID:** `contest-number-repetition`

## Definition

`contest-number-repetition` measures how many numbers from a previous contest are repeated in the next contest.

Since each contest draws **15 numbers from a universe of 25**, at least **5 numbers must always repeat** between two consecutive contests.

## Example

```text
Contest 1:
01, 02, 03, 04, 05, 06, 07, 08, 09, 10, 11, 12, 13, 14, 15

Contest 2:
06, 07, 08, 09, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20
```

Repeated numbers:

```text
06, 07, 08, 09, 10, 11, 12, 13, 14, 15
```

Result:

```text
Repeated: 10
Mandatory minimum: 5
Extra repetitions: 5
```

## Rules

* Compare each contest with the immediately previous contest.
* `repeated` is the total number of common numbers.
* `minimum_repetition` is always `5`.
* `extra_repetitions` represents repetitions above the mandatory minimum.

```text
extra_repetitions = repeated - 5
```

## Historical Analysis

For multiple contests, the rule must calculate:

* Average repeated numbers per contest
* Average extra repetitions above the mandatory minimum
* Minimum observed repetition
* Maximum observed repetition
* Frequency of each repetition count

Example:

```text
5 repeated  → 2 contests
6 repeated  → 8 contests
7 repeated  → 25 contests
8 repeated  → 42 contests
9 repeated  → 31 contests
10 repeated → 15 contests
11 repeated → 4 contests
```

## Expected Output

```json
{
  "rule": "contest-number-repetition",
  "contests_analyzed": 127,
  "average_repeated": 8.12,
  "average_extra_repetitions": 3.12,
  "minimum": 5,
  "maximum": 11,
  "distribution": {
    "5": 2,
    "6": 8,
    "7": 25,
    "8": 42,
    "9": 31,
    "10": 15,
    "11": 4
  }
}
```

