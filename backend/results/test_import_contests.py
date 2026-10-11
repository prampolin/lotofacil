from unittest.mock import Mock, patch

import pytest
import requests
from django.core.management import call_command
from django.core.management.base import CommandError

from results.management.commands.import_contests import TransientImportError
from results.models import Contest

pytestmark = pytest.mark.django_db


@pytest.fixture
def caixa_response():
    return {
        "numero": 3800,
        "dataApuracao": "08/10/2026",
        "listaDezenas": [str(number).zfill(2) for number in range(1, 16)],
    }


@pytest.mark.django_db
def test_import_contest_success(caixa_response):
    response = Mock()
    response.json.return_value = caixa_response
    response.raise_for_status.return_value = None

    with patch(
        "results.management.commands.import_contests.requests.get",
        return_value=response,
    ) as mocked_get:
        call_command("import_contests", number=3800)

    contest = Contest.objects.get(number=3800)

    assert contest.number == 3800
    assert len(contest.numbers) == 15
    assert Contest.objects.count() == 1
    mocked_get.assert_called_once()


@pytest.mark.django_db
def test_import_contest_invalid_numbers(caixa_response):
    caixa_response["listaDezenas"] = ["01", "02", "03"]

    response = Mock()
    response.json.return_value = caixa_response
    response.raise_for_status.return_value = None

    with patch(
        "results.management.commands.import_contests.requests.get",
        return_value=response,
    ):
        with pytest.raises(CommandError):
            call_command("import_contests", number=3800)

    assert Contest.objects.count() == 0


@pytest.mark.parametrize(
    ("status_code", "expected_error"),
    [
        (404, CommandError),
        (503, TransientImportError),
    ],
)
def test_import_contest_http_errors(status_code, expected_error):
    response = Mock()
    response.status_code = status_code

    http_error = requests.HTTPError(response=response)
    response.raise_for_status.side_effect = http_error

    with patch(
        "results.management.commands.import_contests.requests.get",
        return_value=response,
    ):
        with pytest.raises(expected_error):
            call_command("import_contests", number=3800)
