# Rule: Sequence Block Count

**Rule ID:** `sequence-block-count`

## Definition

`sequence-block-count` measures how many independent consecutive-number blocks exist within a contest.

A block is a group of at least **2 consecutive selected numbers**.

## Example

Selected numbers:

```text
01, 02, 03, 06, 07, 10, 11, 12, 13, 18, 21, 22
```

Detected blocks:

```text
01-03
06-07
10-13
21-22
```

Result:

```text
Sequence blocks: 4
```

## Rules

* A block must contain at least 2 consecutive numbers.
* Each independent consecutive sequence counts as one block.
* Isolated numbers do not count as blocks.
* A block can contain any number of consecutive selected numbers.

## Historical Analysis

For multiple contests, calculate:

* Average block count
* Minimum observed count
* Maximum observed count
* Frequency of each block count
* Percentage of contests for each count

## Expected Output

```json
{
  "rule": "sequence-block-count",
  "count": 4,
  "blocks": [
    [1, 2, 3],
    [6, 7],
    [10, 11, 12, 13],
    [21, 22]
  ]
}
```

