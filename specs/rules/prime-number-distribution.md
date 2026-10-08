# Rule: Prime Number Distribution

**Rule ID:** `prime-number-distribution`

## Definition

`prime-number-distribution` analyzes how many prime numbers appear in one or more contests.

## Prime Numbers

Within the Lotofácil universe (`01` to `25`), the prime numbers are:

```text
02, 03, 05, 07, 11, 13, 17, 19, 23
```

There are **9 prime numbers** in total.

## Scope

The rule must support:

* A single contest
* A range of contests
* The last `N` contests
* One or more cycles

## Single Contest Example

```text
Prime numbers drawn:
02, 03, 07, 11, 17, 23

Prime count: 6
Non-prime count: 9
```

## Historical Analysis

For multiple contests, the rule must calculate how often each prime-count pattern occurs.

Example:

```text
3 primes → 5 contests
4 primes → 18 contests
5 primes → 42 contests
6 primes → 31 contests
7 primes → 9 contests
```

## Expected Output

```json
{
  "rule": "prime-number-distribution",
  "contests_analyzed": 105,
  "average_prime_count": 5.14,
  "minimum": 3,
  "maximum": 7,
  "distribution": {
    "3": 5,
    "4": 18,
    "5": 42,
    "6": 31,
    "7": 9
  }
}
```

