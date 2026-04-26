from django.contrib import admin

from apps.documents.models import Document


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = (
        "title", "doc_type", "user", "department", "status",
        "approved_by_dept", "approved_by_dean", "approved_by_rector",
        "academic_year", "created_at",
    )
    list_filter = (
        "status", "doc_type", "academic_year",
        "approved_by_dept", "approved_by_dean", "approved_by_rector",
        "department",
    )
    search_fields = ("title", "user__email", "user__full_name", "department__name")
    autocomplete_fields = ("user", "department")
    readonly_fields = ("id", "created_at", "updated_at", "deleted_at", "approved_at")
    ordering = ("-created_at",)

    fieldsets = (
        (None, {"fields": ("title", "doc_type", "user", "department", "academic_year")}),
        ("Файл", {"fields": ("file_path", "file_size", "mime_type")}),
        ("Согласование", {"fields": (
            "status",
            "approved_by_dept", "approved_by_dean", "approved_by_rector",
            "approved_at", "rejection_reason",
        )}),
        ("Системные", {"fields": ("id", "created_at", "updated_at", "deleted_at")}),
    )

    def get_queryset(self, request):
        return Document.all_objects.select_related("user", "department")
