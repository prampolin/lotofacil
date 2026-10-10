from datetime import date
from types import SimpleNamespace

import pytest

from results.models import Contest
from results.services.statistics import (
    DomainError,
    EmptyDataError,
    statistics,
    stored_statistics,
)


def test_exact_statistics():
    rows = [
        SimpleNamespace(number=3, numbers=list(range(2, 17))),
        SimpleNamespace(number=1, numbers=list(range(1, 16))),
    ]
    result = statistics(rows)
    assert result == statistics(rows[::-1])
    assert result["sample_size"] == 2
    assert result["numbers"][0] == {
        "number": 1,
        "count": 1,
        "frequency_pct": 50.0,
        "draws_since_last_seen": 1,
    }
    assert result["numbers"][1]["frequency_pct"] == 100
    assert result["numbers"][24]["draws_since_last_seen"] is None
    assert result["contests"][0]["repeated_from_previous"] is None
    assert result["aggregates"] == {
        "odd_distribution": {7: 1, 8: 1},
        "even_distribution": {7: 1, 8: 1},
        "sum": {"min": 120, "max": 135, "mean": 127.5},
        "mean_consecutive_pairs": 14.0,
        "mean_repetitions": 14.0,
    }
    assert statistics(rows[:1])["aggregates"]["mean_repetitions"] is None


def test_empty_and_corrupt():
    with pytest.raises(EmptyDataError):
        statistics([])
    with pytest.raises(DomainError):
        statistics([SimpleNamespace(number=1, numbers=[True] * 15)])


@pytest.mark.django_db
def test_selection_one_query(django_assert_num_queries):
    for n in [3, 1, 5]:
        Contest.objects.create(
            number=n, draw_date=date(2020, 1, 1), numbers=list(range(1, 16))
        )
    with django_assert_num_queries(1):
        result = stored_statistics(window=1, as_of_contest=4)
    assert result["last_contest"] == 3
    assert result["sample_size"] == 1
    assert stored_statistics()["sample_size"] == 3


@pytest.mark.parametrize("window", [0, 1001, True, 1.5])
def test_window_validation(window):
    with pytest.raises(DomainError):
        stored_statistics(window=window)
