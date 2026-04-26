from django.contrib import admin

from apps.approvals.models import Approval


@admin.register(Approval)
class ApprovalAdmin(admin.ModelAdmin):
    list_display = (
        "title", "type", "from_user", "department", "status",
        "resolved_by", "resolved_at", "created_at",
    )
    list_filter = ("status", "type", "department")
    search_fields = ("title", "from_user__email", "from_user__full_name")
    autocomplete_fields = ("from_user", "department", "document", "resolved_by")
    readonly_fields = ("id", "created_at", "updated_at", "deleted_at", "resolved_at")
    ordering = ("-created_at",)

    fieldsets = (
        (None, {"fields": ("type", "title", "from_user", "department", "document")}),
        ("Решение", {"fields": ("status", "resolved_by", "resolved_at", "rejection_reason")}),
        ("Системные", {"fields": ("id", "created_at", "updated_at", "deleted_at")}),
    )

    def get_queryset(self, request):
        return Approval.all_objects.select_related("from_user", "department", "document", "resolved_by")
