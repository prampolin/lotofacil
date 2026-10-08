# Rule: Multiple of Three Distribution

**Rule ID:** `multiple-of-three-distribution`

## Definition

`multiple-of-three-distribution` analyzes how many multiples of 3 appear in one or more contests.

## Multiples of Three

Within the Lotofácil universe (`01` to `25`):

```text
03, 06, 09, 12, 15, 18, 21, 24
```

There are **8 multiples of 3** in total.

## Scope

The rule must support:

* A single contest
* A range of contests
* The last `N` contests
* One or more cycles

## Example

```text
Multiples of 3 drawn:
03, 06, 12, 18, 21

Count: 5
```

## Historical Analysis

For multiple contests, calculate:

* Average count
* Minimum observed count
* Maximum observed count
* Frequency of each count
* Percentage of contests for each count

## Expected Output

```json
{
  "rule": "multiple-of-three-distribution",
  "contests_analyzed": 100,
  "average_count": 4.8,
  "minimum": 2,
  "maximum": 7,
  "distribution": {
    "2": 3,
    "3": 14,
    "4": 27,
    "5": 35,
    "6": 17,
    "7": 4
  }
}
```

