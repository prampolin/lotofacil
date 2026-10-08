# Rule: Diagonal Distribution

**Rule ID:** `diagonal-distribution`

## Definition

`diagonal-distribution` analyzes how many drawn numbers belong to the two main diagonals of the 5×5 Lotofácil grid.

## Diagonals

```text
Main diagonal:
01, 07, 13, 19, 25

Secondary diagonal:
05, 09, 13, 17, 21
```

Number `13` belongs to both diagonals but must only be counted once when calculating the total number of diagonal numbers.

Unique diagonal numbers:

```text
01, 05, 07, 09, 13, 17, 19, 21, 25
```

## Example

```text
Main diagonal: 4
Secondary diagonal: 3
Unique diagonal numbers drawn: 6
```

## Rules

* Analyze both diagonals independently.
* Number `13` may contribute to both diagonal counts.
* When calculating the unique total, number `13` must only count once.
* Historical analysis must track the frequency of each diagonal count.

## Expected Output

```json
{
  "rule": "diagonal-distribution",
  "main_diagonal": 4,
  "secondary_diagonal": 3,
  "unique_diagonal_count": 6
}
```

## Historical Analysis

For multiple contests, calculate:

* Average unique diagonal count
* Minimum observed count
* Maximum observed count
* Frequency of each count
* Percentage of contests for each count

