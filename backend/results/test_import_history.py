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
