# Rule: Parity Distribution

**Rule ID:** `parity-distribution`

## Definition

`parity-distribution` analyzes the number of **odd** and **even** numbers drawn in one or more contests.

## Scope

The rule must support:

* A single contest
* A range of contests
* The last `N` contests
* Contests from one or more cycles

## Single Contest Example

```text
Contest 100

Odd: 8
Even: 7
```

Result:

```json
{
  "rule": "parity-distribution",
  "odd": 8,
  "even": 7
}
```

## Multiple Contests

For multiple contests, the rule must calculate the parity distribution of each contest and summarize how often each pattern occurred.

Example:

```text
8 odd / 7 even → 12 contests
7 odd / 8 even → 9 contests
9 odd / 6 even → 4 contests
6 odd / 9 even → 2 contests
```

## Rules

* Odd numbers are numbers not divisible by `2`.
* Even numbers are numbers divisible by `2`.
* Each Lotofácil contest must always total `15` numbers.
* For each contest:

```text
odd + even = 15
```

## Expected Multi-Contest Output

```json
{
  "rule": "parity-distribution",
  "contests": 27,
  "distribution": {
    "8-7": 12,
    "7-8": 9,
    "9-6": 4,
    "6-9": 2
  }
}
```

