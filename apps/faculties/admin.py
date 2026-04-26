from django.contrib import admin

from apps.faculties.models import Faculty


@admin.register(Faculty)
class FacultyAdmin(admin.ModelAdmin):
    list_display = ("name", "short_name", "dean", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("name", "short_name")
    autocomplete_fields = ("dean",)
    readonly_fields = ("id", "created_at", "updated_at", "deleted_at")
    ordering = ("name",)

    def get_queryset(self, request):
        return Faculty.all_objects.all()
