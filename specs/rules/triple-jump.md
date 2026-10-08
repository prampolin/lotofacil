# Rule: Triple Jump

**Rule ID:** `triple-jump`

## Definition

A `triple-jump` occurs when there are exactly **3 consecutive missing numbers** between two selected numbers.

## Condition

```text
next_number - current_number == 4
```

## Example

Selected numbers:

```text
01, 02, 03, 04, 10, 14, 15
```

Between `10` and `14`:

```text
11, 12, 13
```

Result:

```text
triple-jump = true
```

## Invalid Examples

```text
10 -> 12   # 1 missing number
10 -> 13   # 2 missing numbers
10 -> 15   # 4 missing numbers
```

All return:

```text
triple-jump = false
```

## Expected Output

```json
{
  "rule": "triple-jump",
  "matched": true,
  "count": 1
}
```

