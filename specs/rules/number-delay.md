# Rule: Number Delay

**Rule ID:** `number-delay`

## Definition

`number-delay` measures how many consecutive contests have passed since each number last appeared.

## Rules

* A number drawn in the current contest has a delay of `0`.
* A number missing from the current contest increases its delay by `1`.
* The delay resets to `0` when the number appears again.
* Track all numbers from `01` to `25`.

## Example

```text
01 → delay 0
02 → delay 2
03 → delay 1
04 → delay 0
05 → delay 4
```

This means:

* `01` appeared in the current contest.
* `02` has been missing for 2 consecutive contests.
* `05` has been missing for 4 consecutive contests.

## Historical Analysis

For each number, calculate:

* Current delay
* Average delay
* Maximum historical delay
* Frequency of each delay value

## Expected Output

```json
{
  "rule": "number-delay",
  "numbers": {
    "01": {
      "current_delay": 0,
      "average_delay": 0.7,
      "maximum_delay": 5
    },
    "02": {
      "current_delay": 2,
      "average_delay": 0.8,
      "maximum_delay": 6
    }
  }
}
```

