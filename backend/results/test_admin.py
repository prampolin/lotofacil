import pytest
from django.contrib import admin
from django.urls import reverse

from results.models import Contest, SyncExecution


@pytest.mark.parametrize("model", [Contest, SyncExecution])
def test_admin_readonly(model):
    registered = admin.site._registry[model]
    assert not registered.has_add_permission(None)
    assert not registered.has_change_permission(None)
    assert not registered.has_delete_permission(None)
    assert set(registered.get_readonly_fields(None)) == {
        field.name for field in model._meta.fields
    }
    assert registered.list_display


@pytest.mark.django_db
def test_admin_superuser_can_inspect(admin_client, client):
    for model in (Contest, SyncExecution):
        url = reverse(f"admin:results_{model._meta.model_name}_changelist")
        assert admin_client.get(url).status_code == 200
        assert client.get(url).status_code == 302
        assert admin_client.get(url + "add/").status_code == 403
