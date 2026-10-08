# Rule: Rule Transition

**Rule ID:** `rule-transition`

## Definition

`rule-transition` analyzes how the result of one rule changes from one contest to the next.

It measures which values most often follow a given previous value.

## Example

Using `parity-distribution`:

```text
Contest X → 8 odd / 7 even
Contest Y → 7 odd / 8 even
```

This creates the transition:

```text
8-7 → 7-8
```

## Historical Analysis

Example:

```text
After 8-7:

7-8 → 120 times
8-7 → 95 times
9-6 → 60 times
6-9 → 35 times
```

The rule must calculate:

* Number of occurrences
* Transition frequency
* Transition percentage

## Supported Rules

The transition engine should work with rules such as:

```text
parity-distribution
border-number-distribution
column-distribution
group-distribution-repetition
prime-number-distribution
consecutive-number-analysis
contest-number-repetition
```

## Expected Output

```json
{
  "rule": "rule-transition",
  "source_rule": "parity-distribution",
  "from": "8-7",
  "transitions": {
    "7-8": {
      "count": 120,
      "percentage": 38.71
    },
    "8-7": {
      "count": 95,
      "percentage": 30.65
    },
    "9-6": {
      "count": 60,
      "percentage": 19.35
    }
  }
}
```

