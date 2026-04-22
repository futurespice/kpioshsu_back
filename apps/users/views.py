from rest_framework.permissions import IsAuthenticated

from apps.common.permissions import make_role_permission
from apps.common.viewsets import BaseViewSet
from apps.users.models import Role, User
from apps.users.permissions import IsAdmin
from apps.users.serializers import UserSerializer


IsUserLister = make_role_permission(
    Role.ADMIN, Role.RECTOR, Role.VICE_RECTOR, Role.DEAN
)


class UserViewSet(BaseViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        params = self.request.query_params
        if params.get("role"):
            qs = qs.filter(role=params["role"])
        if params.get("dept_id"):
            qs = qs.filter(department_id=params["dept_id"])
        if params.get("faculty_id"):
            qs = qs.filter(faculty_id=params["faculty_id"])
        return qs

    def get_permissions(self):
        if self.action == "list":
            return [IsUserLister()]
        if self.action == "retrieve":
            return [IsAuthenticated()]
        return [IsAdmin()]
