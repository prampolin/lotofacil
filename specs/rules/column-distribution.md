# Rule: Column Distribution

**Rule ID:** `column-distribution`

## Definition

`column-distribution` analyzes how the 15 drawn numbers are distributed across the five vertical columns of the Lotofácil grid.

## Columns

```text
C1: 01, 06, 11, 16, 21
C2: 02, 07, 12, 17, 22
C3: 03, 08, 13, 18, 23
C4: 04, 09, 14, 19, 24
C5: 05, 10, 15, 20, 25
```

## Example

```text
Column distribution:

C1: 3
C2: 2
C3: 4
C4: 3
C5: 3
```

Distribution signature:

```text
3-2-4-3-3
```

## Rules

* Each contest must produce a five-value column signature.
* The sum of all column values must always equal `15`.
* Historical analysis must count how often each distribution occurs.
* The rule must support one contest or multiple contests.

## Expected Output

```json
{
  "rule": "column-distribution",
  "distribution": [3, 2, 4, 3, 3],
  "signature": "3-2-4-3-3"
}
```

