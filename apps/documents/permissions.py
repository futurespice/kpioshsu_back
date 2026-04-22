from rest_framework.permissions import BasePermission

from apps.users.models import Role


class IsDocumentOwnerOrAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        user = request.user
        return obj.user_id == user.id or user.role == Role.ADMIN
