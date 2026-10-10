import pytest


@pytest.fixture(autouse=True)
def block_external_http(monkeypatch):
    def blocked(*args, **kwargs):
        raise AssertionError("HTTP externo proibido nos testes; use mocks.")

    monkeypatch.setattr("requests.sessions.Session.request", blocked)
