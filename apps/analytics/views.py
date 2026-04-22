from django.db.models import Sum
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.approvals.models import Approval, ApprovalStatus
from apps.common.permissions import make_role_permission
from apps.departments.models import Department
from apps.documents.models import Document, DocType
from apps.faculties.models import Faculty
from apps.kpi.models import KPIValue, PeriodType
from apps.kpi.services import (
    calculate_faculty_kpi,
    calculate_university_kpi,
)
from apps.publications.models import Publication
from apps.strategic.models import Grant, GrantStatus, Program, ProgramStatus, StrategicGoal
from apps.strategic.serializers import StrategicGoalSerializer
from apps.tasks.models import Task
from apps.users.models import Role, User


_IsUniReader = make_role_permission(Role.RECTOR, Role.VICE_RECTOR, Role.ADMIN)
_IsRectorOnly = make_role_permission(Role.RECTOR, Role.ADMIN)
_IsViceOnly = make_role_permission(Role.VICE_RECTOR, Role.ADMIN)
_IsDeanOnly = make_role_permission(Role.DEAN, Role.ADMIN)


def _period(request):
    return (
        request.query_params.get("period_type", "month"),
        request.query_params.get("period_value", ""),
    )


class UniversityOverviewView(APIView):
    permission_classes = [_IsUniReader]

    def get(self, request):
        period_type, period_value = _period(request)
        total_kpi = calculate_university_kpi(period_type, period_value)
        return Response(
            {
                "total_kpi": str(total_kpi) if total_kpi is not None else None,
                "teachers_count": User.objects.filter(
                    role=Role.TEACHER, is_active=True
                ).count(),
                "publications_count": Publication.objects.count(),
                "grants_count": Grant.objects.filter(
                    status=GrantStatus.ACTIVE
                ).count(),
                "programs_count": Program.objects.filter(
                    status=ProgramStatus.ACCREDITED
                ).count(),
            }
        )


class UniversityKpiTrendView(APIView):
    permission_classes = [_IsUniReader]

    def get(self, request):
        periods = (
            KPIValue.objects.filter(period_type=PeriodType.MONTH)
            .values_list("period_value", flat=True)
            .distinct()
            .order_by("period_value")
        )
        data = []
        for p in periods:
            k = calculate_university_kpi(PeriodType.MONTH, p)
            data.append(
                {"period": p, "kpi": str(k) if k is not None else None}
            )
        return Response(data)


class UniversityFacultyKpiView(APIView):
    permission_classes = [_IsUniReader]

    def get(self, request):
        period_type, period_value = _period(request)
        data = []
        for f in Faculty.objects.filter(is_active=True):
            k = calculate_faculty_kpi(f.id, period_type, period_value)
            data.append(
                {
                    "name": f.name,
                    "kpi": str(k) if k is not None else None,
                    "trend": None,
                }
            )
        return Response(data)


class UniversityRadarView(APIView):
    permission_classes = [_IsUniReader]

    def get(self, request):
        return Response([])


class UniversityHeatmapView(APIView):
    permission_classes = [_IsUniReader]

    def get(self, request):
        periods = list(
            KPIValue.objects.filter(period_type=PeriodType.MONTH)
            .values_list("period_value", flat=True)
            .distinct()
            .order_by("period_value")
        )
        rows = []
        for f in Faculty.objects.filter(is_active=True):
            cells = {}
            for p in periods:
                k = calculate_faculty_kpi(f.id, PeriodType.MONTH, p)
                cells[p] = str(k) if k is not None else None
            rows.append({"faculty": f.name, "cells": cells})
        return Response({"periods": periods, "rows": rows})


class UniversityGoalsView(APIView):
    permission_classes = [_IsRectorOnly]

    def get(self, request):
        qs = StrategicGoal.objects.filter(
            is_active=True, deleted_at__isnull=True
        )
        year = request.query_params.get("year")
        if year:
            qs = qs.filter(academic_year=year)
        return Response(StrategicGoalSerializer(qs, many=True).data)


class UniversityAlertsView(APIView):
    permission_classes = [_IsRectorOnly]

    def get(self, request):
        return Response([])


class ViceRectorOverviewView(APIView):
    permission_classes = [_IsViceOnly]

    def get(self, request):
        target_sum = (
            Department.objects.aggregate(total=Sum("target_hours"))["total"] or 0
        )
        actual_sum = (
            Task.objects.aggregate(total=Sum("hours"))["total"] or 0
        )
        return Response(
            {
                "approvals_pending": Approval.objects.filter(
                    status=ApprovalStatus.PENDING
                ).count(),
                "tasks_total": Task.objects.count(),
                "dept_target_hours": target_sum,
                "dept_actual_hours": actual_sum,
            }
        )


class ViceRectorDeptLoadView(APIView):
    permission_classes = [_IsViceOnly]

    def get(self, request):
        data = []
        for d in Department.objects.all():
            target = d.target_hours or 0
            actual = (
                Task.objects.filter(to_dept=d).aggregate(total=Sum("hours"))[
                    "total"
                ]
                or 0
            )
            pct = round(actual / target * 100, 2) if target else 0
            data.append(
                {
                    "dept": d.name,
                    "hours": actual,
                    "target": target,
                    "pct": pct,
                }
            )
        return Response(data)


class ViceRectorSuccessDataView(APIView):
    permission_classes = [_IsViceOnly]

    def get(self, request):
        return Response([])


class ViceRectorUmkStatusView(APIView):
    permission_classes = [_IsViceOnly]

    def get(self, request):
        data = []
        for doc in Document.objects.filter(doc_type=DocType.UMK).select_related(
            "department"
        ):
            data.append(
                {
                    "subject": doc.title,
                    "dept": doc.department.name if doc.department else "",
                    "status": doc.status,
                }
            )
        return Response(data)


def _dean_faculty_id(request):
    return request.query_params.get("faculty_id") or getattr(
        request.user, "faculty_id", None
    )


class DeanOverviewView(APIView):
    permission_classes = [_IsDeanOnly]

    def get(self, request):
        faculty_id = _dean_faculty_id(request)
        period_type, period_value = _period(request)
        if faculty_id is None:
            return Response(
                {
                    "faculty_id": None,
                    "departments_count": 0,
                    "teachers_count": 0,
                    "avg_kpi": None,
                    "publications_count": 0,
                    "tasks_count": 0,
                }
            )
        depts = Department.objects.filter(faculty_id=faculty_id)
        teachers = User.objects.filter(
            faculty_id=faculty_id, role=Role.TEACHER, is_active=True
        )
        avg_kpi = calculate_faculty_kpi(faculty_id, period_type, period_value)
        return Response(
            {
                "faculty_id": str(faculty_id),
                "departments_count": depts.count(),
                "teachers_count": teachers.count(),
                "avg_kpi": str(avg_kpi) if avg_kpi is not None else None,
                "publications_count": Publication.objects.filter(
                    user__faculty_id=faculty_id
                ).count(),
                "tasks_count": Task.objects.filter(faculty_id=faculty_id).count(),
            }
        )


class DeanTeachersView(APIView):
    permission_classes = [_IsDeanOnly]

    def get(self, request):
        from apps.kpi.services import read_teacher_kpi_result

        faculty_id = _dean_faculty_id(request)
        period_type, period_value = _period(request)
        teachers = (
            User.objects.filter(
                faculty_id=faculty_id, role=Role.TEACHER, is_active=True
            ).select_related("department")
            if faculty_id
            else User.objects.none()
        )
        data = []
        for t in teachers:
            kpi = read_teacher_kpi_result(t.id, period_type, period_value)
            data.append(
                {
                    "id": str(t.id),
                    "full_name": t.full_name,
                    "email": t.email,
                    "department": t.department.name if t.department else None,
                    "kpi": str(kpi),
                    "publications_count": Publication.objects.filter(
                        user=t
                    ).count(),
                    "tasks_count": Task.objects.filter(to_user=t).count(),
                }
            )
        return Response(data)


class DeanDepartmentsView(APIView):
    permission_classes = [_IsDeanOnly]

    def get(self, request):
        from apps.kpi.services import calculate_department_kpi

        faculty_id = _dean_faculty_id(request)
        period_type, period_value = _period(request)
        depts = (
            Department.objects.filter(faculty_id=faculty_id)
            if faculty_id
            else Department.objects.none()
        )
        data = []
        for d in depts:
            kpi = calculate_department_kpi(d.id, period_type, period_value)
            teachers_count = User.objects.filter(
                department=d, role=Role.TEACHER, is_active=True
            ).count()
            data.append(
                {
                    "id": str(d.id),
                    "name": d.name,
                    "kpi": str(kpi) if kpi is not None else None,
                    "teachers_count": teachers_count,
                    "target_hours": d.target_hours,
                }
            )
        return Response(data)
