from django.contrib import admin

from apps.strategic.models import Grant, Program, StrategicGoal


@admin.register(StrategicGoal)
class StrategicGoalAdmin(admin.ModelAdmin):
    list_display = ("title", "current_value", "target_value", "unit", "progress", "academic_year", "is_active")
    list_filter = ("is_active", "academic_year")
    search_fields = ("title",)
    readonly_fields = ("id", "created_at", "updated_at", "deleted_at")
    ordering = ("-academic_year", "title")

    @admin.display(description="Прогресс, %")
    def progress(self, obj):
        if not obj.target_value:
            return "—"
        return f"{(obj.current_value / obj.target_value * 100):.1f}%"

    def get_queryset(self, request):
        return StrategicGoal.all_objects.all()


@admin.register(Grant)
class GrantAdmin(admin.ModelAdmin):
    list_display = ("title", "amount", "status", "faculty", "year")
    list_filter = ("status", "year", "faculty")
    search_fields = ("title",)
    autocomplete_fields = ("faculty",)
    readonly_fields = ("id", "created_at", "updated_at", "deleted_at")
    ordering = ("-year", "title")

    def get_queryset(self, request):
        return Grant.all_objects.select_related("faculty")


@admin.register(Program)
class ProgramAdmin(admin.ModelAdmin):
    list_display = ("title", "faculty", "status", "accredited_at", "expires_at")
    list_filter = ("status", "faculty")
    search_fields = ("title",)
    autocomplete_fields = ("faculty",)
    readonly_fields = ("id", "created_at", "updated_at", "deleted_at")
    ordering = ("title",)

    def get_queryset(self, request):
        return Program.all_objects.select_related("faculty")
