from django.contrib import admin
from django.utils import timezone

from apps.tasks.models import Task


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = (
        "title", "from_user", "to_user", "to_dept",
        "priority", "status", "deadline", "is_overdue", "points",
    )
    list_filter = ("status", "priority", "faculty", "to_dept")
    search_fields = ("title", "description", "from_user__email", "to_user__email")
    autocomplete_fields = ("from_user", "to_user", "to_dept", "faculty")
    readonly_fields = ("id", "created_at", "updated_at", "deleted_at", "routed_at")
    date_hierarchy = "deadline"
    ordering = ("-created_at",)

    fieldsets = (
        (None, {"fields": ("title", "description", "priority", "status", "points", "hours", "deadline")}),
        ("Маршрутизация", {"fields": ("from_user", "to_user", "to_dept", "faculty", "routed_to", "routed_at")}),
        ("Системные", {"fields": ("id", "created_at", "updated_at", "deleted_at")}),
    )

    @admin.display(boolean=True, description="Просрочена")
    def is_overdue(self, obj):
        return obj.status != "completed" and obj.deadline < timezone.now().date()

    def get_queryset(self, request):
        return Task.all_objects.select_related("from_user", "to_user", "to_dept", "faculty")
