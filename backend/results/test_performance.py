"""Bounded local observations, no unstable wall-clock assertions or live HTTP."""

import json
from datetime import date
from statistics import median
from time import perf_counter

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext
from rest_framework.test import APIClient

from results.models import Contest
from results.services.game_generator import generate_games, reachable_pairs


@pytest.mark.django_db
def test_bounded_local_performance():
    assert connection.settings_dict["NAME"].startswith("test_")
    Contest.objects.bulk_create(
        [
            Contest(number=n, draw_date=date(2020, 1, 1), numbers=list(range(1, 16)))
            for n in range(1, 4001)
        ]
    )
    client = APIClient()
    results = []
    cases = [
        (f"statistics_{n}", "get", f"/api/v1/statistics/?window={n}", None, 200, 1)
        for n in (1, 100, 1000)
    ]
    cases += [
        (
            "generate_100",
            "post",
            "/api/v1/games/generate/",
            {"quantity": 100, "seed": 42},
            200,
            0,
        ),
        (
            "generate_rare",
            "post",
            "/api/v1/games/generate/",
            {
                "quantity": 100,
                "seed": 42,
                "constraints": {"sum_min": 120, "sum_max": 120},
            },
            400,
            0,
        ),
    ]
    for count, quantity in ((10, 10), (200, 100)):
        cases.append(
            (
                f"backtest_{count}x{quantity}",
                "post",
                "/api/v1/backtests/",
                {
                    "mode": "rolling_baseline",
                    "start_contest": 1,
                    "end_contest": count,
                    "quantity": quantity,
                    "seed": 42,
                },
                200,
                1,
            )
        )
    for name, method, url, body, expected, query_count in cases:
        times = []
        for _ in range(3):
            start = perf_counter()
            with CaptureQueriesContext(connection) as queries:
                response = (
                    client.get(url)
                    if method == "get"
                    else client.post(url, body, format="json")
                )
            times.append((perf_counter() - start) * 1000)
            assert response.status_code == expected
            assert len(queries) == query_count
        results.append(
            {
                "case": name,
                "median_ms": round(median(times), 3),
                "max_ms": round(max(times), 3),
                "queries": query_count,
                "bytes": len(response.content),
                "status": expected,
            }
        )
    print("P11_METRICS=" + json.dumps(results))
    print("P11_EXPLAIN=" + Contest.objects.order_by("-number")[:1000].explain())


def test_feasibility_cache_preserves_determinism():
    reachable_pairs.cache_clear()
    started = perf_counter()
    first = generate_games(quantity=100, seed=42)
    cold = perf_counter() - started
    started = perf_counter()
    second = generate_games(quantity=100, seed=42)
    warm = perf_counter() - started
    assert first == second
    assert reachable_pairs.cache_info().misses == 1
    assert reachable_pairs.cache_info().hits == 1
    assert isinstance(reachable_pairs(), frozenset)
    print(f"P11_CACHE cold_ms={cold * 1000:.3f} warm_ms={warm * 1000:.3f}")
