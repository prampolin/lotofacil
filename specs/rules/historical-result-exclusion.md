# Rule: Historical Result Exclusion

**Rule ID:** `historical-result-exclusion`

## Definition

`historical-result-exclusion` rejects any 15-number combination that matches a result already drawn in a previous contest with 15 numbers or shares 14 numbers with any historical contest.

## Condition

A candidate game is considered invalid when:

```text
len(set(candidate_numbers) & set(historical_contest_numbers)) >= 14
```

for any historical contest.

This is equivalent to checking if the candidate matches all 15 numbers, or if any of the candidate's 15 combinations of 14 numbers ($\binom{15}{14}$) is present in the historical pool of 14-number combinations drawn ($N_{\text{contests}} \times 15$).

The order of the numbers does not matter.

## Example 1: 15-number match

Historical result:

```text
01, 02, 03, 05, 06, 07, 09, 10, 11, 13, 15, 18, 20, 22, 25
```

Candidate game:

```text
01, 02, 03, 05, 06, 07, 09, 10, 11, 13, 15, 18, 20, 22, 25
```

Result:

```text
historical-result-exclusion = matched (15 hits)
candidate = rejected
```

## Example 2: 14-number match

Historical result:

```text
01, 02, 03, 05, 06, 07, 09, 10, 11, 13, 15, 18, 20, 22, 25
```

Candidate game:

```text
01, 02, 03, 05, 06, 07, 09, 10, 11, 13, 15, 18, 20, 22, 24
```

Result:

```text
historical-result-exclusion = matched (14 hits)
candidate = rejected
```

## Rules

* Compare the candidate against all historical contest results.
* If 14 or 15 numbers match any historical contest, the rule triggers and rejects the candidate.
* Number order must be ignored.
* Matches with 13 or fewer numbers do not trigger this rule.
* The rule is an exclusion filter, not a prediction rule.

## Expected Output

```json
{
  "rule": "historical-result-exclusion",
  "matched": true,
  "rejected": true,
  "matched_contest": 1234,
  "matched_numbers_count": 14
}
```

