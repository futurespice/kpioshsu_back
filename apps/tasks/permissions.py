from rest_framework.permissions import BasePermission

from apps.users.models import Role


CREATOR_ROLES = {
    Role.ADMIN,
    Role.RECTOR,
    Role.VICE_RECTOR,
    Role.DEAN,
    Role.HEAD_OF_DEPT,
}


class IsTaskCreator(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return user.is_authenticated and user.role in CREATOR_ROLES


class IsTaskOwnerOrAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        user = request.user
        return obj.from_user_id == user.id or user.role == Role.ADMIN


class IsTaskAssignee(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        return obj.to_user_id == request.user.id
