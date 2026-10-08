# Rule: Cycle Number Frequency

**Rule ID:** `cycle-number-frequency`

## Definition

`cycle-number-frequency` measures how many times each number from `01` to `25` appeared within one or more cycles.

## Scope

The rule must support:

* Current cycle
* A specific cycle
* Last `N` cycles
* A custom cycle range

## Example

For the current cycle:

```text
01 → 3
02 → 1
03 → 4
04 → 2
...
25 → 1
```

The value represents how many contests inside the selected cycle scope contained that number.

## Rules

* Each appearance of a number in a contest counts as `1`.
* The same number can accumulate multiple appearances across different contests.
* Frequency is calculated only using contests that belong to the selected cycle scope.
* An open cycle can be analyzed normally.
* Numbers with no appearances must return a frequency of `0`.

## Expected Output

```json
{
  "rule": "cycle-number-frequency",
  "scope": {
    "type": "current-cycle",
    "cycles": [38]
  },
  "frequencies": {
    "01": 3,
    "02": 1,
    "03": 4,
    "04": 2,
    "05": 3,
    "25": 1
  }
}
```

## Multi-Cycle Example

```json
{
  "rule": "cycle-number-frequency",
  "scope": {
    "type": "last-n-cycles",
    "count": 5
  },
  "frequencies": {
    "01": 18,
    "02": 15,
    "03": 21,
    "04": 17,
    "25": 14
  }
}
```
:wq

