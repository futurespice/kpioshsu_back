from django.contrib import admin

from apps.notifications.models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("title", "user", "type", "is_read", "created_at")
    list_filter = ("type", "is_read")
    search_fields = ("title", "message", "user__email", "user__full_name")
    autocomplete_fields = ("user",)
    readonly_fields = ("id", "created_at", "updated_at", "deleted_at")
    ordering = ("-created_at",)
    actions = ("mark_read", "mark_unread")

    @admin.action(description="Отметить как прочитанные")
    def mark_read(self, request, queryset):
        queryset.update(is_read=True)

    @admin.action(description="Отметить как непрочитанные")
    def mark_unread(self, request, queryset):
        queryset.update(is_read=False)

    def get_queryset(self, request):
        return Notification.all_objects.select_related("user")
