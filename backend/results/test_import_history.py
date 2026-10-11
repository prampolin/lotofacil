from datetime import date
from unittest.mock import patch

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

from results.management.commands.import_contests import TransientImportError
from results.models import Contest


@pytest.mark.django_db
def test_import_history_skips_existing_contests():
    Contest.objects.create(
        number=3800,
        draw_date=date(2026, 10, 8),
        numbers=list(range(1, 16)),
    )

    with patch(
        "results.management.commands.import_history.call_command"
    ) as mocked_command:
        call_command(
            "import_history",
            start=3800,
            end=3800,
        )

    mocked_command.assert_not_called()


@pytest.mark.django_db
def test_import_history_imports_missing_contests():
    with (
        patch(
            "results.management.commands.import_history.call_command"
        ) as mocked_command,
        patch("results.management.commands.import_history.time.sleep"),
    ):
        call_command(
            "import_history",
            start=3798,
            end=3800,
            delay=1,
        )

    assert mocked_command.call_count == 3
    assert mocked_command.call_args_list[0].kwargs == {"number": 3798}
    assert mocked_command.call_args_list[1].kwargs == {"number": 3799}
    assert mocked_command.call_args_list[2].kwargs == {"number": 3800}


@pytest.mark.django_db
def test_import_history_retries_after_failure():
    with (
        patch(
            "results.management.commands.import_history.call_command"
        ) as mocked_command,
        patch("results.management.commands.import_history.time.sleep") as mocked_sleep,
    ):
        mocked_command.side_effect = [
            TransientImportError("Erro temporário"),
            None,
        ]

        call_command(
            "import_history",
            start=3790,
            end=3790,
        )

    assert mocked_command.call_count == 2
    mocked_sleep.assert_called_once_with(2)


@pytest.mark.django_db
def test_import_history_does_not_retry_permanent_errors():
    with (
        patch(
            "results.management.commands.import_history.call_command"
        ) as mocked_command,
        patch("results.management.commands.import_history.time.sleep") as mocked_sleep,
    ):
        mocked_command.side_effect = CommandError("Erro permanente HTTP 404")

        with pytest.raises(CommandError):
            call_command(
                "import_history",
                start=3790,
                end=3790,
            )

    mocked_command.assert_called_once_with(
        "import_contests",
        number=3790,
    )

    mocked_sleep.assert_not_called()


@pytest.mark.django_db
@pytest.mark.parametrize("delay, pauses", [(1, [2, 4]), (5, [5, 5])])
def test_retry_respects_minimum_delay(delay, pauses):
    with (
        patch("results.management.commands.import_history.call_command") as importer,
        patch("results.management.commands.import_history.time.sleep") as sleep,
    ):
        importer.side_effect = [TransientImportError("timeout")] * 2 + [None]
        call_command("import_history", start=1, end=1, delay=delay)
    assert [c.args[0] for c in sleep.call_args_list] == pauses
    assert importer.call_count == 3


@pytest.mark.parametrize(
    "header, expected",
    [
        ("12", 12),
        (" 0 ", 0),
        ("-1", 0),
        ("1.5", 0),
        ("invalid", 0),
        (None, 0),
        ("9" * 5000, 301),
        ("Wed, 21 Oct 2015 07:28:00 GMT", 0),
    ],
)
def test_retry_after_parser(header, expected):
    from results.management.commands.import_contests import retry_after_seconds

    assert retry_after_seconds(header) == expected


def test_retry_after_http_date():
    from datetime import datetime, timezone

    from results.management.commands.import_contests import retry_after_seconds

    with patch("results.management.commands.import_contests.datetime") as clock:
        clock.now.return_value = datetime(2015, 10, 21, 7, 27, tzinfo=timezone.utc)
        assert retry_after_seconds("Wed, 21 Oct 2015 07:28:00 GMT") == 60


@pytest.mark.django_db
@pytest.mark.parametrize("status", [429, 503])
def test_retry_after_from_http_response(status):
    from unittest.mock import Mock

    import requests

    response = requests.Response()
    response.status_code = status
    response.headers["Retry-After"] = "12"
    failed = Mock()
    failed.raise_for_status.side_effect = requests.HTTPError(response=response)
    success = Mock()
    success.json.return_value = {
        "numero": 1,
        "dataApuracao": "01/01/2020",
        "listaDezenas": list(range(1, 16)),
    }
    with (
        patch(
            "results.management.commands.import_contests.requests.get",
            side_effect=[failed, success],
        ) as get,
        patch("results.management.commands.import_history.time.sleep") as sleep,
    ):
        call_command("import_history", start=1, end=1, delay=5)
    sleep.assert_called_once_with(12)
    assert get.call_count == 2
    assert Contest.objects.filter(number=1).count() == 1


@pytest.mark.django_db
def test_long_retry_after_stops_without_early_retry():
    error = TransientImportError("HTTP 429", retry_after=301)
    with (
        patch(
            "results.management.commands.import_history.call_command", side_effect=error
        ) as importer,
        patch("results.management.commands.import_history.time.sleep") as sleep,
        pytest.raises(CommandError, match="retome mais tarde") as raised,
    ):
        call_command("import_history", start=1, end=1)
    assert raised.value.__cause__ is error
    importer.assert_called_once()
    sleep.assert_not_called()
