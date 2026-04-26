from django.contrib import admin

from apps.department_load.models import DeptLoad


@admin.register(DeptLoad)
class DeptLoadAdmin(admin.ModelAdmin):
    list_display = ("department", "academic_year", "semester", "target_hours", "actual_hours", "load_pct")
    list_filter = ("academic_year", "semester", "department__faculty")
    search_fields = ("department__name", "department__short")
    autocomplete_fields = ("department",)
    readonly_fields = ("id", "created_at", "updated_at", "deleted_at")
    ordering = ("-academic_year", "-semester")

    @admin.display(description="Выполнение, %")
    def load_pct(self, obj):
        if not obj.target_hours:
            return "—"
        return f"{(obj.actual_hours / obj.target_hours * 100):.1f}%"

    def get_queryset(self, request):
        return DeptLoad.all_objects.select_related("department")
