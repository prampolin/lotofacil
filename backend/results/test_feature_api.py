from datetime import date

import pytest
from rest_framework.test import APIClient

from results.models import Contest


@pytest.fixture
def client():
    return APIClient()


@pytest.fixture
def draws(db):
    for n in [1, 3, 5]:
        Contest.objects.create(
            number=n, draw_date=date(2020, 1, 1), numbers=list(range(1, 16))
        )


def test_health(client):
    assert client.get("/api/v1/health/").json() == {
        "status": "ok",
        "service": "lotofacil-api",
        "version": "1.0.0",
    }


def test_statistics_api(client, draws):
    response = client.get("/api/v1/statistics/?window=1&as_of_contest=4")
    assert response.status_code == 200
    assert response.data["sample_size"] == 1
    assert response.data["last_contest"] == 3
    assert response.data["numbers"][0]["frequency_pct"] == 100
    assert client.get("/api/v1/results/latest/").data["number"] == 5


@pytest.mark.parametrize(
    "query", ["window=0", "window=1001", "window=abc", "as_of_contest=-1", "unknown=1"]
)
def test_invalid_queries(client, query):
    assert client.get("/api/v1/statistics/?" + query).status_code == 400


@pytest.mark.django_db
def test_empty(client):
    assert client.get("/api/v1/statistics/").status_code == 404
    assert client.get("/api/v1/results/latest/").status_code == 404
    assert (
        client.post(
            "/api/v1/backtests/",
            {"mode": "rolling_baseline", "start_contest": 1, "end_contest": 3},
            format="json",
        ).status_code
        == 404
    )


def test_generation_no_db(client):
    body = {"quantity": 2, "seed": 42, "constraints": {"odd_min": 6}}
    first = client.post("/api/v1/games/generate/", body, format="json")
    assert first.status_code == 200
    assert (
        first.data == client.post("/api/v1/games/generate/", body, format="json").data
    )
    assert len(first.data["games"]) == 2


@pytest.mark.parametrize(
    "body",
    [
        {"quantity": True},
        {"quantity": 1.1},
        {"quantity": "2"},
        {"seed": 2**63},
        {"constraints": {"wat": 1}},
        {"constraints": None},
        {"constraints": {"sum_max": 119}},
        {"quantity": 0},
        {"other": 2},
        [],
        {"constraints": {"odd_max": 2}},
    ],
)
def test_bad_generation(client, body):
    response = client.post("/api/v1/games/generate/", body, format="json")
    assert response.status_code == 400


def test_backtest_api(client, draws):
    body = {
        "mode": "fixed_games",
        "start_contest": 1,
        "end_contest": 3,
        "games": [list(range(1, 16))],
        "seed": 42,
    }
    response = client.post("/api/v1/backtests/", body, format="json")
    assert response.status_code == 200
    assert response.data["avg_hits"] == 15
    assert response.data["missing_count"] == 1
    assert response.data["draw_count"] == 2
    assert response.data == client.post("/api/v1/backtests/", body, format="json").data


@pytest.mark.parametrize(
    "extra",
    [
        {"mode": "other"},
        {"mode": "fixed_games"},
        {"start_contest": 4},
        {"games": [[1] * 15]},
        {"quantity": 101},
        {"quantity": True},
    ],
)
def test_invalid_backtest(client, extra):
    body = {"mode": "rolling_baseline", "start_contest": 1, "end_contest": 3, **extra}
    assert client.post("/api/v1/backtests/", body, format="json").status_code == 400


def test_bad_json_and_methods(client):
    assert (
        client.post(
            "/api/v1/games/generate/", "{", content_type="application/json"
        ).status_code
        == 400
    )
    assert client.get("/api/v1/games/generate/").status_code == 405


def test_corrupt_data_and_no_writes(client, draws):
    before = list(Contest.objects.values_list("number", "numbers"))
    client.post("/api/v1/games/generate/", {"seed": 1}, format="json")
    client.post(
        "/api/v1/backtests/",
        {"mode": "rolling_baseline", "start_contest": 1, "end_contest": 5},
        format="json",
    )
    assert list(Contest.objects.values_list("number", "numbers")) == before
    Contest.objects.filter(number=5).update(numbers=[1])
    assert client.get("/api/v1/statistics/").status_code == 400
    assert (
        client.post(
            "/api/v1/backtests/",
            {"mode": "rolling_baseline", "start_contest": 1, "end_contest": 5},
            format="json",
        ).status_code
        == 400
    )


@pytest.mark.django_db
def test_backtest_query_cap(client, django_assert_num_queries):
    Contest.objects.bulk_create(
        [
            Contest(number=n, draw_date=date(2020, 1, 1), numbers=list(range(1, 16)))
            for n in range(1, 202)
        ]
    )
    with django_assert_num_queries(1):
        response = client.post(
            "/api/v1/backtests/",
            {"mode": "rolling_baseline", "start_contest": 1, "end_contest": 201},
            format="json",
        )
    assert response.status_code == 400
