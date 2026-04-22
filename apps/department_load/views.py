from rest_framework import mixins, viewsets

from apps.common.permissions import make_role_permission
from apps.department_load.models import DeptLoad
from apps.department_load.serializers import DeptLoadSerializer
from apps.users.models import Role
from apps.users.permissions import IsAdmin, IsManagement


_IsRetrieveReader = make_role_permission(Role.DEAN, Role.VICE_RECTOR, Role.ADMIN)
_IsLoadEditor = make_role_permission(Role.ADMIN, Role.HEAD_OF_DEPT)


class DeptLoadViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    queryset = DeptLoad.objects.all()
    serializer_class = DeptLoadSerializer
    lookup_value_regex = "[0-9a-f-]{36}"

    def get_queryset(self):
        return super().get_queryset().filter(deleted_at__isnull=True)

    def get_permissions(self):
        if self.action == "list":
            return [IsManagement()]
        if self.action == "retrieve":
            return [_IsRetrieveReader()]
        if self.action in ("update", "partial_update"):
            return [_IsLoadEditor()]
        return [IsAdmin()]
