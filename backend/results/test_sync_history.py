from datetime import date
from unittest.mock import Mock, call, patch

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

from results.models import Contest, SyncExecution


@pytest.fixture
def mock_caixa():
    response = Mock()
    response.json.return_value = {"numero": 10}
    response.raise_for_status.return_value = None

    with patch(
        "results.management.commands.sync_history.requests.get",
        return_value=response,
    ) as mocked_get:
        yield mocked_get


@pytest.mark.django_db
def test_sync_history_dry_run_does_not_import(mock_caixa):
    with patch(
        "results.management.commands.sync_history.call_command"
    ) as mocked_command:
        call_command(
            "sync_history",
            start=1,
            batch_size=5,
            limit=5,
            dry_run=True,
        )

    mocked_command.assert_not_called()
    mock_caixa.assert_called_once()


@pytest.mark.django_db
def test_sync_history_skips_existing_contests(mock_caixa):
    Contest.objects.create(
        number=1,
        draw_date=date(2003, 9, 29),
        numbers=list(range(1, 16)),
    )

    with (
        patch(
            "results.management.commands.sync_history.call_command"
        ) as mocked_command,
        patch("results.management.commands.sync_history.time.sleep"),
    ):
        call_command(
            "sync_history",
            start=1,
            batch_size=3,
            limit=3,
        )

    assert mocked_command.call_args_list == [
        call("import_history", start=2, end=2),
        call("import_history", start=3, end=3),
        call("import_history", start=4, end=4),
    ]


@pytest.mark.django_db
def test_sync_history_respects_limit(mock_caixa):
    with (
        patch(
            "results.management.commands.sync_history.call_command"
        ) as mocked_command,
        patch("results.management.commands.sync_history.time.sleep"),
    ):
        call_command(
            "sync_history",
            start=1,
            batch_size=2,
            limit=3,
        )

    assert mocked_command.call_count == 3


@pytest.mark.django_db
def test_sync_history_imports_in_order(mock_caixa):
    with (
        patch(
            "results.management.commands.sync_history.call_command"
        ) as mocked_command,
        patch("results.management.commands.sync_history.time.sleep"),
    ):
        call_command(
            "sync_history",
            start=5,
            batch_size=2,
            limit=3,
        )

    assert mocked_command.call_args_list == [
        call("import_history", start=5, end=5),
        call("import_history", start=6, end=6),
        call("import_history", start=7, end=7),
    ]


@pytest.mark.django_db
def test_sync_history_creates_completed_execution(mock_caixa):
    with (
        patch(
            "results.management.commands.sync_history.call_command"
        ) as mocked_command,
        patch("results.management.commands.sync_history.time.sleep"),
    ):
        call_command(
            "sync_history",
            start=1,
            batch_size=2,
            limit=3,
        )

    execution = SyncExecution.objects.get()

    assert execution.status == "completed"
    assert execution.start_contest == 1
    assert execution.end_contest == 3
    assert execution.processed == 3
    assert execution.finished_at is not None
    assert execution.error_message == ""
    assert mocked_command.call_count == 3


@pytest.mark.django_db
def test_sync_history_records_failed_execution(mock_caixa):
    with (
        patch(
            "results.management.commands.sync_history.call_command"
        ) as mocked_command,
        patch("results.management.commands.sync_history.time.sleep"),
    ):
        mocked_command.side_effect = [
            None,
            CommandError("Falha simulada"),
        ]

        with pytest.raises(CommandError):
            call_command(
                "sync_history",
                start=1,
                batch_size=3,
                limit=3,
            )

    execution = SyncExecution.objects.get()

    assert execution.status == "failed"
    assert execution.processed == 1
    assert execution.finished_at is not None
    assert "Falha simulada" in execution.error_message
    assert mocked_command.call_count == 2
