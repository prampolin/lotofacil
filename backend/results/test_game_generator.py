import random
from unittest.mock import patch

import pytest

from results.services.game_generator import generate_games
from results.services.statistics import DomainError


def test_seed_invariants_and_global_rng():
    state = random.getstate()
    result = generate_games(100, 42)
    assert result == generate_games(100, 42)
    assert random.getstate() == state
    assert len({tuple(game) for game in result["games"]}) == 100
    for game in result["games"]:
        assert game == sorted(set(game))
        assert len(game) == 15
        assert min(game) >= 1 and max(game) <= 25


def test_filters():
    result = generate_games(
        10, 7, {"odd_min": 7, "odd_max": 7, "sum_min": 180, "sum_max": 200}
    )
    for game in result["games"]:
        assert sum(n % 2 for n in game) == 7
        assert 180 <= sum(game) <= 200


@pytest.mark.parametrize(
    "constraints",
    [
        {"other": 1},
        [],
        {"odd_min": 10, "odd_max": 5},
        {"sum_min": 271},
        {"odd_max": 2},
        {"sum_max": 120, "odd_max": 7},
        {"odd_min": True},
    ],
)
def test_bad_constraints(constraints):
    with pytest.raises(DomainError):
        generate_games(constraints=constraints)


@pytest.mark.parametrize("quantity", [0, 101, True, 1.2])
def test_quantity(quantity):
    with pytest.raises(DomainError):
        generate_games(quantity)


def test_attempts_exhausted():
    with patch(
        "results.services.game_generator.random.Random.sample",
        return_value=list(range(1, 16)),
    ) as sample:
        with pytest.raises(DomainError, match="10000"):
            generate_games(2, 1)
    assert sample.call_count == 10000


def test_seed_bounds():
    with pytest.raises(DomainError):
        generate_games(seed=2**63)
