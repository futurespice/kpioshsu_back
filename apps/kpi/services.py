from decimal import Decimal

from apps.departments.models import Department
from apps.faculties.models import Faculty
from apps.kpi.models import KPIResult, KPIValue
from apps.users.models import Role, User


def _clamp(value: Decimal) -> Decimal:
    return min(max(value, Decimal("0")), Decimal("100"))


def calculate_teacher_kpi(user_id, period_type: str, period_value: str) -> Decimal:
    """КПЭ преподавателя = Σ(value × weight), clamped [0, 100], quantize 0.01.

    Формула по ТЗ v2 §4.1 (без деления на 100).
    """
    values = KPIValue.objects.filter(
        user_id=user_id,
        period_type=period_type,
        period_value=period_value,
        kpi__is_active=True,
    ).select_related("kpi")

    if not values.exists():
        return Decimal("0.00")

    total = sum((v.value * v.kpi.weight for v in values), start=Decimal("0"))
    return _clamp(total).quantize(Decimal("0.01"))


def upsert_kpi_result(user_id, period_type, period_value) -> KPIResult:
    """Пересчитать КПЭ преподавателя и обновить/создать KPIResult.

    Вызывается после POST /api/kpi/value (ТЗ v2 §4.2).
    """
    total = calculate_teacher_kpi(user_id, period_type, period_value)
    obj, _ = KPIResult.objects.update_or_create(
        user_id=user_id,
        period_type=period_type,
        period_value=period_value,
        defaults={"total_value": total},
    )
    return obj


def read_teacher_kpi_result(user_id, period_type, period_value) -> Decimal:
    """Прочитать КПЭ преподавателя из KPIResult. 0.00 если записи нет."""
    obj = KPIResult.objects.filter(
        user_id=user_id,
        period_type=period_type,
        period_value=period_value,
    ).first()
    return obj.total_value if obj else Decimal("0.00")


def calculate_department_kpi(department_id, period_type, period_value):
    """КПЭ кафедры = среднее КПЭ активных TEACHER. None если преподавателей нет.

    Читает из KPIResult (агрегаты по ТЗ v2 §4.2 работают с уже посчитанными данными).
    """
    teachers = User.objects.filter(
        department_id=department_id,
        role=Role.TEACHER,
        is_active=True,
    )
    if not teachers.exists():
        return None

    kpis = [
        read_teacher_kpi_result(t.id, period_type, period_value) for t in teachers
    ]
    avg = sum(kpis, Decimal("0")) / len(kpis)
    return avg.quantize(Decimal("0.01"))


def calculate_faculty_kpi(faculty_id, period_type, period_value):
    """КПЭ факультета = среднее КПЭ кафедр. None если нет кафедр с данными."""
    depts = Department.objects.filter(faculty_id=faculty_id)
    if not depts.exists():
        return None

    dept_kpis = [
        calculate_department_kpi(d.id, period_type, period_value) for d in depts
    ]
    dept_kpis = [k for k in dept_kpis if k is not None]
    if not dept_kpis:
        return None

    avg = sum(dept_kpis, Decimal("0")) / len(dept_kpis)
    return avg.quantize(Decimal("0.01"))


def calculate_university_kpi(period_type, period_value):
    """КПЭ университета = среднее КПЭ факультетов (только активные)."""
    faculties = Faculty.objects.filter(is_active=True)
    if not faculties.exists():
        return None

    fac_kpis = [
        calculate_faculty_kpi(f.id, period_type, period_value) for f in faculties
    ]
    fac_kpis = [k for k in fac_kpis if k is not None]
    if not fac_kpis:
        return None

    avg = sum(fac_kpis, Decimal("0")) / len(fac_kpis)
    return avg.quantize(Decimal("0.01"))
