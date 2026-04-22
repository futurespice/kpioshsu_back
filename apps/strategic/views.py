from rest_framework.permissions import IsAuthenticated

from apps.common.permissions import make_role_permission
from apps.common.viewsets import BaseViewSet
from apps.strategic.models import Grant, Program, StrategicGoal
from apps.strategic.serializers import (
    GrantSerializer,
    ProgramSerializer,
    StrategicGoalSerializer,
)
from apps.users.models import Role
from apps.users.permissions import IsAdmin, IsManagement


_IsGoalEditor = make_role_permission(Role.ADMIN, Role.RECTOR)


class StrategicGoalViewSet(BaseViewSet):
    queryset = StrategicGoal.objects.all()
    serializer_class = StrategicGoalSerializer
    lookup_value_regex = "[0-9a-f-]{36}"

    def get_queryset(self):
        qs = super().get_queryset()
        year = self.request.query_params.get("year")
        if year:
            qs = qs.filter(academic_year=year)
        return qs

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [IsManagement()]
        if self.action in ("update", "partial_update"):
            return [_IsGoalEditor()]
        return [IsAdmin()]


class GrantViewSet(BaseViewSet):
    queryset = Grant.objects.all()
    serializer_class = GrantSerializer
    lookup_value_regex = "[0-9a-f-]{36}"

    def get_queryset(self):
        qs = super().get_queryset()
        p = self.request.query_params
        if p.get("year"):
            qs = qs.filter(year=p["year"])
        if p.get("status"):
            qs = qs.filter(status=p["status"])
        return qs

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [IsManagement()]
        return [IsAdmin()]


class ProgramViewSet(BaseViewSet):
    queryset = Program.objects.all()
    serializer_class = ProgramSerializer
    lookup_value_regex = "[0-9a-f-]{36}"

    def get_queryset(self):
        qs = super().get_queryset()
        p = self.request.query_params
        if p.get("faculty_id"):
            qs = qs.filter(faculty_id=p["faculty_id"])
        if p.get("status"):
            qs = qs.filter(status=p["status"])
        return qs

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [IsAuthenticated()]
        return [IsAdmin()]
