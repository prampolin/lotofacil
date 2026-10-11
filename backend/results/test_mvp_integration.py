"""P09: contracts exercised through HTTP and the isolated PostgreSQL database."""

from datetime import date
from time import perf_counter

import pytest
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test.utils import CaptureQueriesContext
from rest_framework.test import APIClient

from results.models import Contest, SyncExecution

pytestmark = pytest.mark.django_db


def seed_draws(numbers=(1, 3, 5)):
    Contest.objects.bulk_create(
        [
            Contest(number=n, draw_date=date(2020, 1, 1), numbers=list(range(1, 16)))
            for n in numbers
        ]
    )


def post(client, path, body):
    return client.post(f"/api/v1/{path}/", body, format="json")


def test_postgres_isolation_migrations_and_unique_index():
    assert connection.vendor == "postgresql"
    with connection.cursor() as cursor:
        cursor.execute("SELECT current_database()")
        assert cursor.fetchone()[0] == "test_lotofacil"
        constraints = connection.introspection.get_constraints(
            cursor, Contest._meta.db_table
        )
    assert any(c["unique"] and c["columns"] == ["number"] for c in constraints.values())
    executor = MigrationExecutor(connection)
    executor.loader.check_consistent_history(connection)
    assert executor.migration_plan(executor.loader.graph.leaf_nodes()) == []


def test_generated_tickets_flow_into_fixed_backtest(django_assert_num_queries):
    seed_draws()
    client = APIClient()
    before = list(Contest.objects.values())
    with django_assert_num_queries(0):
        generated = post(client, "games/generate", {"quantity": 100, "seed": -(2**63)})
        replay = post(client, "games/generate", {"quantity": 100, "seed": -(2**63)})
    assert generated.status_code == 200
    assert generated.json() == replay.json()
    games = generated.json()["games"]
    assert len({tuple(g) for g in games}) == 100
    assert all(g == sorted(set(g)) and len(g) == 15 for g in games)
    with django_assert_num_queries(1):
        response = post(
            client,
            "backtests",
            dict(
                mode="fixed_games", start_contest=1, end_contest=5, games=games, seed=7
            ),
        )
    assert response.status_code == 200
    data = response.json()
    expected = [len(set(g) & set(range(1, 16))) for g in games]
    assert data["comparisons"] == data["baseline"]["comparisons"] == 300
    assert data["missing_count"] == 2
    assert sum(data["distribution"].values()) == 300
    assert data["avg_hits"] == round(sum(expected) / 100, 4)
    assert all(row["hits"] == expected for row in data["contests"])
    assert list(Contest.objects.values()) == before
    assert SyncExecution.objects.count() == 0


def test_http_future_mutation_and_prefix_invariance():
    seed_draws()
    client = APIClient()
    body = dict(
        mode="rolling_baseline", start_contest=1, end_contest=5, quantity=3, seed=7
    )
    original = post(client, "backtests", body).json()
    assert original == post(client, "backtests", body).json()
    prefix = post(client, "backtests", {**body, "end_contest": 1}).json()
    assert original["contests"][0] == prefix["contests"][0]
    Contest.objects.all().update(numbers=list(range(11, 26)))
    seed_draws((6,))
    changed = post(client, "backtests", body).json()
    assert [r["games"] for r in original["contests"]] == [
        r["games"] for r in changed["contests"]
    ]
    assert changed["draw_count"] == 3


def test_http_results_statistics_gaps_and_empty_selection(django_assert_num_queries):
    seed_draws((5, 1, 3))
    client = APIClient()
    for path in ("results/latest/", "results/5/"):
        with django_assert_num_queries(1):
            response = client.get("/api/v1/" + path)
        assert response.status_code == 200
        assert response.json() == {
            "number": 5,
            "draw_date": "2020-01-01",
            "numbers": list(range(1, 16)),
        }
    with django_assert_num_queries(1):
        response = client.get("/api/v1/statistics/?window=1000&as_of_contest=4")
    data = response.json()
    assert response.status_code == 200
    assert data["sample_size"] == 2
    assert [r["number"] for r in data["contests"]] == [1, 3]
    assert data["aggregates"]["sum"] == {"min": 120, "max": 120, "mean": 120}
    assert data["aggregates"]["mean_repetitions"] == 15
    assert data["numbers"][-1]["draws_since_last_seen"] is None
    assert client.get("/api/v1/results/2/").status_code == 404
    assert (
        post(
            client,
            "backtests",
            dict(mode="rolling_baseline", start_contest=2, end_contest=2),
        ).status_code
        == 404
    )


def test_maximum_http_workload_and_query_bounds():
    seed_draws(range(1, 1002))
    client = APIClient()
    started = perf_counter()
    with CaptureQueriesContext(connection) as queries:
        stats = client.get("/api/v1/statistics/?window=1000")
        result = post(
            client,
            "backtests",
            dict(
                mode="rolling_baseline",
                start_contest=1,
                end_contest=200,
                quantity=100,
                seed=42,
            ),
        )
    elapsed = perf_counter() - started
    assert stats.status_code == result.status_code == 200
    assert stats.json()["sample_size"] == 1000
    assert result.json()["comparisons"] == 20000
    assert len(queries) == 2
    assert "LIMIT 1000" in queries[0]["sql"]
    assert "LIMIT 201" in queries[1]["sql"]
    print(
        f"P09 max workload: {elapsed:.3f}s; backtest JSON={len(result.content)} bytes; queries=2"
    )


@pytest.mark.parametrize("path", ["games/generate", "backtests"])
def test_malformed_http_json(path):
    response = APIClient().post(
        f"/api/v1/{path}/", "{", content_type="application/json"
    )
    assert response.status_code == 400
    assert "detail" in response.json()


@pytest.mark.parametrize(
    "path,method",
    [
        ("statistics", "post"),
        ("backtests", "get"),
        ("results/latest", "post"),
        ("results/1", "post"),
    ],
)
def test_http_wrong_methods(path, method):
    response = getattr(APIClient(), method)(f"/api/v1/{path}/")
    assert response.status_code == 405
    assert "detail" in response.json()
