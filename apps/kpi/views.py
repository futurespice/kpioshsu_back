from rest_framework import status, viewsets
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.common.permissions import make_role_permission
from apps.kpi.models import KPI, KPIValue
from apps.kpi.serializers import KPISerializer, KPIValueSerializer
from apps.kpi.services import (
    calculate_department_kpi,
    calculate_faculty_kpi,
    calculate_university_kpi,
    read_teacher_kpi_result,
    upsert_kpi_result,
)
from apps.users.models import Role
from apps.users.permissions import IsAdmin, IsHeadOfDept


_IsDeptKpiReader = make_role_permission(Role.DEAN, Role.HEAD_OF_DEPT, Role.ADMIN)
_IsFacultyKpiReader = make_role_permission(
    Role.RECTOR, Role.VICE_RECTOR, Role.DEAN, Role.ADMIN
)
_IsUniKpiReader = make_role_permission(Role.RECTOR, Role.VICE_RECTOR, Role.ADMIN)


class KPIViewSet(viewsets.ModelViewSet):
    serializer_class = KPISerializer
    lookup_value_regex = "[0-9a-f-]{36}"

    def get_queryset(self):
        qs = KPI.objects.filter(deleted_at__isnull=True)
        if self.action == "list":
            qs = qs.filter(is_active=True)
        return qs

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [IsAuthenticated()]
        if self.action == "destroy":
            return [IsAdmin()]
        return [IsHeadOfDept()]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.is_active = False
        instance.save(update_fields=["is_active"])
        return Response(status=status.HTTP_204_NO_CONTENT)


class KPIValueCreateView(APIView):
    permission_classes = [IsHeadOfDept]

    def post(self, request):
        serializer = KPIValueSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        upsert_kpi_result(
            instance.user_id, instance.period_type, instance.period_value
        )
        return Response(
            KPIValueSerializer(instance).data, status=status.HTTP_201_CREATED
        )


class KPIValueListView(ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = KPIValueSerializer

    def get_queryset(self):
        return KPIValue.objects.filter(
            user_id=self.kwargs["user_id"], deleted_at__isnull=True
        )


class TeacherKPIResultView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, user_id):
        period_type = request.query_params.get("period_type", "month")
        period_value = request.query_params.get("period_value", "")
        result = read_teacher_kpi_result(user_id, period_type, period_value)
        return Response(
            {
                "user": str(user_id),
                "total_value": str(result),
                "period_type": period_type,
                "period_value": period_value,
            }
        )


class DepartmentKPIResultView(APIView):
    permission_classes = [_IsDeptKpiReader]

    def get(self, request, department_id):
        period_type = request.query_params.get("period_type", "month")
        period_value = request.query_params.get("period_value", "")
        result = calculate_department_kpi(department_id, period_type, period_value)
        return Response(
            {
                "department": str(department_id),
                "total_value": str(result) if result is not None else None,
                "period_type": period_type,
                "period_value": period_value,
            }
        )


class FacultyKPIResultView(APIView):
    permission_classes = [_IsFacultyKpiReader]

    def get(self, request, faculty_id):
        period_type = request.query_params.get("period_type", "month")
        period_value = request.query_params.get("period_value", "")
        result = calculate_faculty_kpi(faculty_id, period_type, period_value)
        return Response(
            {
                "faculty": str(faculty_id),
                "total_value": str(result) if result is not None else None,
                "period_type": period_type,
                "period_value": period_value,
            }
        )


class UniversityKPIResultView(APIView):
    permission_classes = [_IsUniKpiReader]

    def get(self, request):
        period_type = request.query_params.get("period_type", "month")
        period_value = request.query_params.get("period_value", "")
        result = calculate_university_kpi(period_type, period_value)
        return Response(
            {
                "total_value": str(result) if result is not None else None,
                "period_type": period_type,
                "period_value": period_value,
            }
        )
