from rest_framework.permissions import BasePermission


def make_role_permission(*roles):
    """Фабрика permission-классов по ролям.

    Использование: `IsAdmin = make_role_permission(Role.ADMIN)`.
    Роль пользователя читается из `request.user.role`.
    """
    class RolePermission(BasePermission):
        def has_permission(self, request, view):
            user = request.user
            return bool(
                user
                and user.is_authenticated
                and getattr(user, "role", None) in roles
            )

    return RolePermission
