from django.contrib import admin

from apps.planerka.models import Planerka


@admin.register(Planerka)
class PlanerkaAdmin(admin.ModelAdmin):
    list_display = ("title", "faculty", "priority", "status", "deadline", "points", "hours", "created_by")
    list_filter = ("priority", "status")
    search_fields = ("title", "description", "faculty")
    autocomplete_fields = ("created_by",)
    readonly_fields = ("id", "created_at", "updated_at", "deleted_at")
    date_hierarchy = "deadline"
    ordering = ("-deadline",)

    def get_queryset(self, request):
        return Planerka.all_objects.select_related("created_by")
