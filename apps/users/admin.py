from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.contrib.auth.forms import UserChangeForm, UserCreationForm

from apps.users.models import User


class UserCreationFormCustom(UserCreationForm):
    class Meta:
        model = User
        fields = ("email",)


class UserChangeFormCustom(UserChangeForm):
    class Meta:
        model = User
        fields = "__all__"


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    form = UserChangeFormCustom
    add_form = UserCreationFormCustom

    list_display = ("email", "full_name", "role", "faculty", "department", "is_active", "is_staff")
    list_filter = ("role", "is_active", "is_staff", "faculty", "department")
    search_fields = ("email", "full_name")
    ordering = ("-created_at",)
    autocomplete_fields = ("faculty", "department")
    filter_horizontal = ("groups", "user_permissions")
    readonly_fields = ("id", "created_at", "updated_at", "deleted_at", "last_login")

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Профиль", {"fields": ("full_name", "role", "faculty", "department")}),
        ("Доступы", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Системные", {"fields": ("id", "last_login", "created_at", "updated_at", "deleted_at")}),
    )
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "password1", "password2", "full_name", "role"),
        }),
    )

    def get_queryset(self, request):
        return User.all_objects.all()
