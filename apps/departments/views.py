from rest_framework.permissions import IsAuthenticated

from apps.common.viewsets import BaseViewSet
from apps.departments.models import Department
from apps.departments.serializers import DepartmentSerializer
from apps.users.permissions import IsAdmin


class DepartmentViewSet(BaseViewSet):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [IsAuthenticated()]
        return [IsAdmin()]

    def get_queryset(self):
        qs = super().get_queryset()
        faculty_id = self.request.query_params.get("faculty_id")
        if faculty_id:
            qs = qs.filter(faculty_id=faculty_id)
        return qs
