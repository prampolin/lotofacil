import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from unittest.mock import Mock, patch

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import connections
from django.test import override_settings
from rest_framework.test import APIClient

from results.models import Contest, SyncExecution
from results.services.import_lock import import_lock


def test_production_settings_fail_closed():
    env = {k: v for k, v in os.environ.items() if not k.startswith("DJANGO_")}
    command = [sys.executable, "-c", "import config.production"]
    absent = subprocess.run(command, env=env, capture_output=True, text=True)
    assert absent.returncode != 0
    assert "DJANGO_SECRET_KEY is required" in absent.stderr
    env["DJANGO_SECRET_KEY"] = "django-insecure-" + "a" * 64
    weak = subprocess.run(command, env=env, capture_output=True, text=True)
    assert weak.returncode != 0
    env["DJANGO_SECRET_KEY"] = "test-only-strong-key-0123456789" * 3
    missing_hosts = subprocess.run(command, env=env, capture_output=True, text=True)
    assert missing_hosts.returncode != 0
    env["DJANGO_ALLOWED_HOSTS"] = "example.test"
    env["POSTGRES_PASSWORD"] = "test-only"
    valid = subprocess.run(
        [
            sys.executable,
            "manage.py",
            "check",
            "--deploy",
            "--settings=config.production",
            "--fail-level=WARNING",
        ],
        env=env,
        capture_output=True,
        text=True,
    )
    assert valid.returncode == 0, valid.stderr


@override_settings(DEBUG=False, ALLOWED_HOSTS=["testserver"])
def test_public_access_hosts_cors_and_security_headers():
    client = APIClient()
    response = client.post(
        "/api/v1/games/generate/",
        {"seed": 1},
        format="json",
        HTTP_ORIGIN="https://untrusted.test",
    )
    assert response.status_code == 200
    assert "Access-Control-Allow-Origin" not in response
    assert response["X-Content-Type-Options"] == "nosniff"
    assert response["X-Frame-Options"] == "DENY"
    assert client.get("/api/v1/health/", HTTP_HOST="evil.test").status_code == 400
    assert client.get("/admin/").status_code == 302


@override_settings(DEBUG=False)
def test_internal_error_does_not_expose_traceback():
    client = APIClient(raise_request_exception=False)
    with patch(
        "results.views.GenerateGamesView.service",
        side_effect=RuntimeError("PRIVATE_SENTINEL"),
    ):
        response = client.post("/api/v1/games/generate/", {}, format="json")
    assert response.status_code == 500
    assert b"PRIVATE_SENTINEL" not in response.content
    assert b"Traceback" not in response.content


@pytest.mark.parametrize("path", ["games/generate", "backtests"])
def test_large_json_rejected_before_service(path):
    with (
        patch("results.views.GenerateGamesView.service") as generate,
        patch("results.views.BacktestView.service") as backtest,
    ):
        response = APIClient().post(
            f"/api/v1/{path}/",
            '{"junk":"' + "x" * 65536 + '"}',
            content_type="application/json",
        )
    assert response.status_code == 413
    generate.assert_not_called()
    backtest.assert_not_called()


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize(
    "command,options",
    [
        ("sync_history", {}),
        ("import_history", {"start": 1, "end": 1}),
        ("import_contests", {"number": 1}),
    ],
)
def test_concurrent_importer_rejected_before_http(command, options):
    def second_connection():
        try:
            with pytest.raises(CommandError, match="Outro importador"):
                call_command(command, **options)
        finally:
            connections.close_all()

    with (
        patch("requests.get") as get,
        import_lock(),
        ThreadPoolExecutor(max_workers=1) as pool,
    ):
        pool.submit(second_connection).result(timeout=5)
        get.assert_not_called()
    assert not Contest.objects.exists()
    assert not SyncExecution.objects.exists()
    # Released lock permits a subsequent run, including nested entrypoints.
    with import_lock(), import_lock():
        pass


@pytest.mark.django_db
def test_interruption_logs_failure_and_resume_skips_saved_draw():
    def import_one(name, start, end, delay):
        if start == 2:
            raise KeyboardInterrupt
        Contest.objects.create(
            number=1, draw_date=date(2020, 1, 1), numbers=list(range(1, 16))
        )

    with (
        patch("requests.get", return_value=Mock(json=lambda: {"numero": 2})),
        patch("time.sleep"),
        patch(
            "results.management.commands.sync_history.call_command",
            side_effect=import_one,
        ),
    ):
        with pytest.raises(KeyboardInterrupt):
            call_command("sync_history")
    log = SyncExecution.objects.get()
    assert log.status == "failed" and log.processed == 1
    assert log.finished_at and log.error_message == "KeyboardInterrupt"
    with (
        patch("requests.get", return_value=Mock(json=lambda: {"numero": 2})),
        patch("time.sleep"),
        patch("results.management.commands.sync_history.call_command") as importer,
    ):
        call_command("sync_history")
        assert importer.call_count == 1
        assert importer.call_args.kwargs["start"] == 2


@pytest.mark.django_db
def test_sync_large_remote_number_has_bounded_selection():
    from io import StringIO

    output = StringIO()
    with patch("requests.get", return_value=Mock(json=lambda: {"numero": 2147483647})):
        call_command("sync_history", start=1, limit=25, dry_run=True, stdout=output)
    assert "Concursos selecionados: 25" in output.getvalue()
    assert "Concursos ausentes: 2147483647" in output.getvalue()
    assert not SyncExecution.objects.exists()


def test_deep_json_is_a_client_error():
    client = APIClient(raise_request_exception=False)
    response = client.post(
        "/api/v1/games/generate/",
        "[" * 2000 + "0" + "]" * 2000,
        content_type="application/json",
    )
    assert response.status_code == 400


def test_body_limit_without_content_length():
    from django.test import RequestFactory

    from config.middleware import APIBodyLimitMiddleware

    request = RequestFactory().post(
        "/api/v1/games/generate/", b"x" * 65537, content_type="application/json"
    )
    request.META.pop("CONTENT_LENGTH")
    handler = Mock()
    response = APIBodyLimitMiddleware(handler)(request)
    assert response.status_code == 413
    handler.assert_not_called()


@pytest.mark.django_db(transaction=True)
def test_lock_released_after_exception():
    with pytest.raises(RuntimeError), import_lock():
        raise RuntimeError("interrupted")

    def acquire_from_new_session():
        try:
            with import_lock():
                return True
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=1) as pool:
        assert pool.submit(acquire_from_new_session).result(timeout=5)


@pytest.mark.parametrize("hosts", ["*", ",", "*.example.test"])
def test_production_rejects_unsafe_hosts(hosts):
    env = {
        **os.environ,
        "DJANGO_SECRET_KEY": "test-only-strong-key-0123456789" * 3,
        "DJANGO_ALLOWED_HOSTS": hosts,
    }
    result = subprocess.run(
        [sys.executable, "-c", "import config.production"],
        env=env,
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert "explicit DJANGO_ALLOWED_HOSTS" in result.stderr
