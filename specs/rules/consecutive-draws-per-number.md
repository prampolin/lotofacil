# Rule: Consecutive Draws per Number (Sequência Consecutiva de Saídas)

**Rule ID:** `consecutive-draws-per-number`

## Definition

`consecutive-draws-per-number` measures the number of consecutive contests in which a specific number (from `01` to `25`) was drawn without interruption, tracking the maximum historical streak, all periods of occurrence, the current streak, and the overall streak distribution across the lottery history.

## Rules

* When a number appears in a contest, its active streak increments by `1`.
* When a number fails to appear in a contest, its active streak resets to `0`.
* A sequence requires at least `1` contest presence.
* When the active streak terminates (or reaches the latest available contest), the length and start/end contests are recorded.
* The maximum streak ever achieved is calculated for each number `01` to `25`.
* If a number achieved its maximum streak in more than one distinct historical window, all occurrences are tracked.
* Current streak tracks how many consecutive contests ending at the most recent contest the number has been drawn in (0 if absent in the most recent contest).

## Example

```text
Contest 10: [03, ...] -> 03 streak = 1 (start: 10)
Contest 11: [03, ...] -> 03 streak = 2
Contest 12: [03, ...] -> 03 streak = 3
Contest 13: [02, ...] -> 03 fails -> streak ended at 3 (conc. 10 to 12)
```

## Historical Insights (Lotofácil)

* **All-time Record:** Number `07` appeared in **25 consecutive contests** (from contest `2866` to `2890`).
* **Runner-up:** Number `25` appeared in **21 consecutive contests** (from contest `3183` to `3203`).
* **Number 03 Record:** Number `03` reached **18 consecutive contests** (from contest `852` to `869`).
* Over 40% of streaks are of length 1 (drawn once and missing in the next contest).
* Streaks of 15 or more consecutive contests are extremely rare (< 0.1% of all sequences).

## Expected Output

```json
{
  "total_contests": 3781,
  "overall_record": {
    "number": 7,
    "max_streak": 25,
    "max_occurrences": [[2866, 2890]]
  },
  "results_by_number": {
    "07": {
      "max_streak": 25,
      "max_occurrences": [[2866, 2890]],
      "current_streak": 3,
      "total_draws": 2231,
      "avg_streak": 2.35
    }
  }
}
```
