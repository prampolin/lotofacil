from datetime import date

import pytest

from results.models import Contest
from results.services.contest_service import save_contest


@pytest.fixture
def contest_data():
    return {
        "numero": 3800,
        "dataApuracao": "08/10/2026",
        "listaDezenas": [str(n).zfill(2) for n in range(1, 16)],
    }


@pytest.mark.django_db
def test_save_contest_creates_record(contest_data):
    contest, created = save_contest(contest_data)
    assert created is True

    assert contest.number == 3800
    assert contest.draw_date == date(2026, 10, 8)
    assert Contest.objects.count() == 1


@pytest.mark.django_db
def test_save_contest_updates_existing_record(contest_data):
    first_contest, first_created = save_contest(contest_data)
    second_contest, second_created = save_contest(contest_data)

    assert first_created is True
    assert second_created is False
    assert first_contest.pk == second_contest.pk
    assert Contest.objects.count() == 1


@pytest.mark.django_db
@pytest.mark.parametrize(
    "invalid",
    [
        [1] * 15,
        list(range(15)),
        list(range(12, 27)),
        [True] + list(range(2, 16)),
        list(range(1, 15)),
    ],
)
def test_invalid_model_numbers(invalid):
    from django.core.exceptions import ValidationError

    contest = Contest(number=1, draw_date=date(2020, 1, 1), numbers=invalid)
    with pytest.raises(ValidationError):
        contest.full_clean()


@pytest.mark.django_db
def test_model_positive_and_normalized(contest_data):
    from django.core.exceptions import ValidationError

    contest_data["listaDezenas"].reverse()
    contest, _ = save_contest(contest_data)
    assert contest.numbers == list(range(1, 16))
    contest.number = 0
    with pytest.raises(ValidationError):
        contest.full_clean()
    contest.refresh_from_db()
    assert contest.number == 3800


@pytest.mark.django_db
def test_bad_import_does_not_change_existing(contest_data):
    from django.core.exceptions import ValidationError

    original, _ = save_contest(contest_data)
    contest_data["listaDezenas"] = ["01"] * 15
    with pytest.raises(ValidationError):
        save_contest(contest_data)
    original.refresh_from_db()
    assert original.numbers == list(range(1, 16))
