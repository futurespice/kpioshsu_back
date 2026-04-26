from django.contrib import admin

from apps.kpi.models import KPI, KPIResult, KPIValue


@admin.register(KPI)
class KPIAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "weight", "is_active", "created_by", "created_at")
    list_filter = ("category", "is_active")
    search_fields = ("name", "description")
    autocomplete_fields = ("created_by",)
    readonly_fields = ("id", "created_at", "updated_at", "deleted_at")
    ordering = ("name",)

    def get_queryset(self, request):
        return KPI.all_objects.all()


@admin.register(KPIValue)
class KPIValueAdmin(admin.ModelAdmin):
    list_display = ("user", "kpi", "value", "period_type", "period_value", "created_at")
    list_filter = ("period_type", "kpi__category", "kpi")
    search_fields = ("user__email", "user__full_name", "kpi__name", "period_value")
    autocomplete_fields = ("user", "kpi")
    readonly_fields = ("id", "created_at", "updated_at", "deleted_at")
    ordering = ("-created_at",)

    def get_queryset(self, request):
        return KPIValue.all_objects.select_related("user", "kpi")


@admin.register(KPIResult)
class KPIResultAdmin(admin.ModelAdmin):
    list_display = ("user", "total_value", "period_type", "period_value", "created_at")
    list_filter = ("period_type",)
    search_fields = ("user__email", "user__full_name", "period_value")
    autocomplete_fields = ("user",)
    readonly_fields = ("id", "created_at", "updated_at", "deleted_at")
    ordering = ("-created_at",)

    def get_queryset(self, request):
        return KPIResult.all_objects.select_related("user")
