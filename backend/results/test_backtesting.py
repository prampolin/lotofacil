from types import SimpleNamespace

import pytest

from results.services.backtesting import evaluate
from results.services.statistics import DomainError, EmptyDataError


def row(n, start=1):
    return SimpleNamespace(number=n, numbers=list(range(start, start + 15)))


def test_exact_hits_gaps_inclusive_and_baseline():
    result = evaluate(
        [row(4), row(3, 11), row(1), row(0)],
        1,
        3,
        "fixed_games",
        [list(range(1, 16))],
        seed=42,
    )
    assert result["draw_count"] == 2
    assert result["missing_count"] == 1
    assert result["comparisons"] == result["baseline"]["comparisons"] == 2
    assert result["distribution"][15] == result["distribution"][5] == 1
    assert result["avg_hits"] == 10
    assert all(result["distribution"][n] == 0 for n in range(5))


def test_baseline_cannot_see_target_or_future():
    original = evaluate(
        [row(1), row(2), row(3)], 1, 3, "rolling_baseline", quantity=3, seed=7
    )
    changed = evaluate(
        [row(1, 11), row(2, 11), row(3, 11)],
        1,
        3,
        "rolling_baseline",
        quantity=3,
        seed=7,
    )
    prefix = evaluate([row(1)], 1, 1, "rolling_baseline", quantity=3, seed=7)
    assert [r["games"] for r in original["contests"]] == [
        r["games"] for r in changed["contests"]
    ]
    assert original["contests"][0] == prefix["contests"][0]
    assert original == evaluate(
        [row(3), row(1), row(2)], 1, 3, "rolling_baseline", quantity=3, seed=7
    )
    assert original["distribution"] == original["baseline"]["distribution"]


@pytest.mark.parametrize(
    "kwargs",
    [
        dict(mode="bad"),
        dict(mode="fixed_games"),
        dict(mode="fixed_games", games=[[1] * 15]),
        dict(mode="rolling_baseline", games=[]),
        dict(mode="rolling_baseline", quantity=101),
        dict(mode="fixed_games", games=[list(range(1, 16))], quantity=1),
    ],
)
def test_invalid_config(kwargs):
    with pytest.raises(DomainError):
        evaluate([row(1)], 1, 1, **kwargs)


def test_empty_range_and_cap():
    with pytest.raises(EmptyDataError):
        evaluate([], 1, 1, "rolling_baseline")
    with pytest.raises(DomainError):
        evaluate([row(n) for n in range(1, 202)], 1, 201, "rolling_baseline")
    with pytest.raises(DomainError):
        evaluate([], 2, 1, "rolling_baseline")
    assert (
        evaluate([row(n) for n in range(1, 201)], 1, 200, "rolling_baseline")[
            "draw_count"
        ]
        == 200
    )
