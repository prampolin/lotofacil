from django.contrib import admin

from .models import Contest, SyncExecution


class ReadOnlyAdmin(admin.ModelAdmin):
    def get_readonly_fields(self, request, obj=None):
        return tuple(field.name for field in self.model._meta.fields)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Contest)
class ContestAdmin(ReadOnlyAdmin):
    list_display = ("number", "draw_date", "created_at")
    list_filter = ("draw_date",)
    search_fields = ("=number",)
    ordering = ("-number",)


@admin.register(SyncExecution)
class SyncExecutionAdmin(ReadOnlyAdmin):
    list_display = (
        "id",
        "status",
        "start_contest",
        "end_contest",
        "processed",
        "started_at",
        "finished_at",
    )
    list_filter = ("status", "started_at")
    search_fields = ("=id",)
