from datetime import date
from unittest.mock import Mock, patch

import pytest
import requests
from django.core.management import call_command
from django.core.management.base import CommandError

from results.management.commands.import_contests import TransientImportError
from results.models import Contest, SyncExecution

pytestmark = pytest.mark.django_db


@pytest.fixture
def network():
    with patch("requests.get", return_value=Mock(json=lambda: {"numero": 3})) as get:
        yield get


@pytest.mark.django_db
def test_resume_noop_and_dry_run(network):
    with patch("results.management.commands.sync_history.time.sleep"):
        call_command("sync_history", dry_run=True)
        assert not SyncExecution.objects.exists()
        assert not Contest.objects.exists()

        def importer(name, start, end, delay):
            if start == 2:
                raise CommandError("stop")
            Contest.objects.create(
                number=start, draw_date=date(2020, 1, 1), numbers=list(range(1, 16))
            )

        with patch(
            "results.management.commands.sync_history.call_command",
            side_effect=importer,
        ):
            with pytest.raises(CommandError):
                call_command("sync_history")
        assert SyncExecution.objects.get().processed == 1
        with patch("results.management.commands.sync_history.call_command") as nested:
            call_command("sync_history")
        assert [c.kwargs["start"] for c in nested.call_args_list] == [2, 3]
        for n in [2, 3]:
            Contest.objects.create(
                number=n, draw_date=date(2020, 1, 1), numbers=list(range(1, 16))
            )
        count = SyncExecution.objects.count()
        call_command("sync_history")
        assert SyncExecution.objects.count() == count


@pytest.mark.parametrize(
    "options",
    [
        {"start": 0},
        {"limit": 101},
        {"batch_size": 0},
        {"delay": float("nan")},
        {"delay": float("inf")},
        {"delay": 0},
    ],
)
def test_invalid_options_before_network(options, network):
    with pytest.raises(CommandError):
        call_command("sync_history", **options)
    network.assert_not_called()


@pytest.mark.django_db
def test_logging_failure_preserves_original(network):
    with (
        patch(
            "results.management.commands.sync_history.call_command",
            side_effect=CommandError("original"),
        ),
        patch.object(SyncExecution, "save", autospec=True) as save,
    ):
        save.side_effect = [None, RuntimeError("logging")]
        with pytest.raises(CommandError, match="original"):
            call_command("sync_history")


@pytest.mark.parametrize(
    "error",
    [
        requests.Timeout(),
        requests.ConnectionError(),
        requests.HTTPError(response=Mock(status_code=429)),
    ],
)
def test_transient_network_errors(error):
    with patch("requests.get", side_effect=error), pytest.raises(TransientImportError):
        call_command("import_contests", number=1)


@pytest.mark.parametrize(
    "payload",
    [{}, {"numero": 2}, {"numero": 1, "dataApuracao": "bad", "listaDezenas": []}],
)
def test_bad_payload(payload):
    with (
        patch("requests.get", return_value=Mock(json=lambda: payload)),
        pytest.raises(CommandError),
    ):
        call_command("import_contests", number=1)


@pytest.mark.django_db
def test_retry_cap():
    with (
        patch(
            "results.management.commands.import_history.call_command",
            side_effect=TransientImportError("retry"),
        ) as nested,
        patch("results.management.commands.import_history.time.sleep"),
    ):
        with pytest.raises(CommandError, match="3 tentativas"):
            call_command("import_history", start=1, end=1)
    assert nested.call_count == 3
