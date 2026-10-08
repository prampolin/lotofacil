# Candidate Generation and Filter Pipeline

## Candidate Pool

**ID:** `candidate-pool`

The `candidate-pool` generates all possible 15-number combinations based on the previous contest.

Each candidate is composed of:

* `R` numbers selected from the 15 numbers of the previous contest.
* `15 - R` numbers selected from the remaining 10 numbers.

## Repetition Range

The generator must support selecting which repetition counts are allowed.

Example:

```text
Allowed repetitions:
14, 13, 12, 11, 10, 9, 8
```

Only candidates matching one of these repetition counts must be generated.

## Combination Counts

```text
15 repeated →       1
14 repeated →     150
13 repeated →   4,725
12 repeated →  54,600
11 repeated → 286,650
10 repeated → 756,756
 9 repeated → 1,051,050
 8 repeated → 772,200
 7 repeated → 289,575
 6 repeated →  50,050
 5 repeated →   3,003
```

## Filter Pipeline

**ID:** `filter-pipeline`

The `filter-pipeline` applies rules sequentially to the candidate pool.

Each filter can either:

* Require a rule to match.
* Require a rule not to match.
* Restrict a rule to an allowed range or value.

## Example

Initial candidate pool:

```text
3,268,759 candidates
```

Apply:

```text
triple-jump = required
```

The system must remove every candidate where:

```text
triple-jump = false
```

Pipeline:

```text
Candidate Pool
      ↓
Triple Jump
      ↓
Remove non-matches
      ↓
Remaining Candidates
      ↓
Next Rule
      ↓
Remaining Candidates
```

## Filter Statistics

Every filter operation must record:

```json
{
  "rule": "triple-jump",
  "condition": "required",
  "input_count": 3268759,
  "removed_count": 0,
  "remaining_count": 0
}
```

## Example Pipeline

```text
Generate candidates
        ↓
Repetition: 8–14
        ↓
Historical Result Exclusion
        ↓
Triple Jump: required
        ↓
Parity Distribution: allowed range
        ↓
Prime Number Distribution
        ↓
Border Number Distribution
        ↓
Consecutive Number Analysis
        ↓
Final Candidate Pool
```

## Important Requirement

Filters must be independent and composable.

Adding, removing, or changing one filter must not require modifying the candidate generator or other rules.

