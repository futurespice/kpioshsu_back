from django.contrib import admin

from apps.departments.models import Department


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ("name", "short", "faculty", "head", "target_hours", "created_at")
    list_filter = ("faculty",)
    search_fields = ("name", "short")
    autocomplete_fields = ("faculty", "head")
    readonly_fields = ("id", "created_at", "updated_at", "deleted_at")
    ordering = ("name",)

    def get_queryset(self, request):
        return Department.all_objects.all()
