# Rule: Fibonacci Number Distribution

**Rule ID:** `fibonacci-number-distribution`

## Definition

`fibonacci-number-distribution` analyzes how many Fibonacci numbers appear in one or more contests.

## Fibonacci Numbers

Within the Lotofácil universe (`01` to `25`):

```text
01, 02, 03, 05, 08, 13, 21
```

## Scope

The rule must support:

* A single contest
* A range of contests
* The last `N` contests
* One or more cycles

## Example

```text
Fibonacci numbers drawn:
01, 03, 05, 13, 21

Fibonacci count: 5
```

## Historical Analysis

For multiple contests, calculate:

* Average Fibonacci count
* Minimum observed count
* Maximum observed count
* Frequency of each count
* Percentage of contests for each count

## Expected Output

```json
{
  "rule": "fibonacci-number-distribution",
  "contests_analyzed": 100,
  "average_fibonacci_count": 4.2,
  "minimum": 2,
  "maximum": 6,
  "distribution": {
    "2": 4,
    "3": 18,
    "4": 39,
    "5": 31,
    "6": 8
  }
}
```

