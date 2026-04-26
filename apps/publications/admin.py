from django.contrib import admin

from apps.publications.models import Publication


@admin.register(Publication)
class PublicationAdmin(admin.ModelAdmin):
    list_display = (
        "title", "user", "journal_type", "journal",
        "pub_date", "kpi_points_display", "academic_year", "is_archived",
    )
    list_filter = ("journal_type", "is_archived", "academic_year")
    search_fields = ("title", "journal", "user__email", "user__full_name", "coauthors")
    autocomplete_fields = ("user", "kpi_indicator")
    readonly_fields = ("id", "created_at", "updated_at", "deleted_at", "kpi_points_display")
    date_hierarchy = "pub_date"
    ordering = ("-pub_date",)

    fieldsets = (
        (None, {"fields": ("user", "title", "journal", "journal_type", "pub_date", "academic_year")}),
        ("Дополнительно", {"fields": ("url", "coauthors", "evidence_file", "kpi_indicator", "kpi_points_display", "is_archived")}),
        ("Системные", {"fields": ("id", "created_at", "updated_at", "deleted_at")}),
    )

    @admin.display(description="Баллы КПЭ")
    def kpi_points_display(self, obj):
        return obj.kpi_points

    def get_queryset(self, request):
        return Publication.all_objects.select_related("user", "kpi_indicator")
