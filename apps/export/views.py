from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.common.permissions import make_role_permission
from apps.departments.models import Department
from apps.export.utils import require_xlsx, xlsx_response
from apps.faculties.models import Faculty
from apps.kpi.models import KPIValue
from apps.kpi.services import (
    calculate_department_kpi,
    read_teacher_kpi_result,
)
from apps.publications.models import Publication
from apps.tasks.models import Task
from apps.users.models import Role, User


_IsDeptKpiReader = make_role_permission(Role.DEAN, Role.HEAD_OF_DEPT, Role.ADMIN)
_IsFacultyKpiReader = make_role_permission(
    Role.RECTOR, Role.VICE_RECTOR, Role.DEAN, Role.ADMIN
)
_IsRectorOnly = make_role_permission(Role.RECTOR, Role.ADMIN)


def _period(request):
    return (
        request.query_params.get("period_type", "month"),
        request.query_params.get("period_value", ""),
    )


class TeacherKPIExportView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, user_id):
        require_xlsx(request)
        period_type, period_value = _period(request)
        values = KPIValue.objects.filter(
            user_id=user_id,
            period_type=period_type,
            period_value=period_value,
        ).select_related("kpi")
        rows = [
            (v.kpi.name, str(v.value), str(v.kpi.weight), str(v.value * v.kpi.weight))
            for v in values
        ]
        return xlsx_response(
            ["Показатель", "Значение", "Вес", "Баллы"],
            rows,
            f"kpi_teacher_{user_id}",
        )


class DepartmentKPIExportView(APIView):
    permission_classes = [_IsDeptKpiReader]

    def get(self, request, department_id):
        require_xlsx(request)
        period_type, period_value = _period(request)
        teachers = User.objects.filter(
            department_id=department_id, role=Role.TEACHER, is_active=True
        )
        rows = [
            (
                t.full_name or t.email,
                t.email,
                str(read_teacher_kpi_result(t.id, period_type, period_value)),
            )
            for t in teachers
        ]
        return xlsx_response(
            ["Преподаватель", "Email", "КПЭ"],
            rows,
            f"kpi_department_{department_id}",
        )


class FacultyKPIExportView(APIView):
    permission_classes = [_IsFacultyKpiReader]

    def get(self, request, faculty_id):
        require_xlsx(request)
        period_type, period_value = _period(request)
        depts = Department.objects.filter(faculty_id=faculty_id)
        rows = []
        for d in depts:
            kpi = calculate_department_kpi(d.id, period_type, period_value)
            rows.append((d.name, str(kpi) if kpi is not None else ""))
        return xlsx_response(
            ["Кафедра", "КПЭ"], rows, f"kpi_faculty_{faculty_id}"
        )


class TasksExportView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        require_xlsx(request)
        qs = Task.objects.filter(deleted_at__isnull=True).select_related(
            "from_user", "to_user"
        )
        p = request.query_params
        if p.get("status"):
            qs = qs.filter(status=p["status"])
        if p.get("priority"):
            qs = qs.filter(priority=p["priority"])
        if p.get("from"):
            qs = qs.filter(from_user_id=p["from"])
        if p.get("to"):
            qs = qs.filter(to_user_id=p["to"])
        rows = [
            (
                t.title,
                t.priority,
                t.status,
                t.deadline.isoformat() if t.deadline else "",
                t.from_user.email if t.from_user else "",
                t.to_user.email if t.to_user else "",
                t.points,
            )
            for t in qs
        ]
        return xlsx_response(
            ["Название", "Приоритет", "Статус", "Дедлайн", "От", "Кому", "Баллы"],
            rows,
            "tasks",
        )


class PublicationsExportView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, user_id):
        require_xlsx(request)
        qs = Publication.objects.filter(
            user_id=user_id, deleted_at__isnull=True
        )
        year = request.query_params.get("year")
        if year:
            qs = qs.filter(academic_year=year)
        rows = [
            (
                p.title,
                p.journal,
                p.journal_type,
                p.pub_date.isoformat(),
                p.academic_year,
                p.kpi_points,
            )
            for p in qs
        ]
        return xlsx_response(
            ["Название", "Журнал", "Тип", "Дата", "Учебный год", "Баллы"],
            rows,
            f"publications_{user_id}",
        )


class UniversityReportExportView(APIView):
    permission_classes = [_IsRectorOnly]

    def get(self, request):
        require_xlsx(request)
        period_type, period_value = _period(request)
        from apps.kpi.services import calculate_faculty_kpi

        rows = []
        for f in Faculty.objects.filter(is_active=True):
            k = calculate_faculty_kpi(f.id, period_type, period_value)
            rows.append((f.name, str(k) if k is not None else ""))
        return xlsx_response(
            ["Факультет", "КПЭ"], rows, "university_report"
        )
