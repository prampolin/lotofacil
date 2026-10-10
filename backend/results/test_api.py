from datetime import date

import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from results.models import Contest


@pytest.mark.django_db
def test_get_existing_contest():
    contest = Contest.objects.create(
        number=3800,
        draw_date=date(2026, 10, 8),
        numbers=list(range(1, 16)),
    )

    client = APIClient()

    url = reverse("contest-detail", kwargs={"number": 3800})
    response = client.get(url)

    assert response.status_code == 200
    assert response.data["number"] == contest.number
    assert response.data["numbers"] == list(range(1, 16))


@pytest.mark.django_db
def test_get_nonexistent_contest():
    client = APIClient()

    url = reverse("contest-detail", kwargs={"number": 999999})
    response = client.get(url)

    assert response.status_code == 404
