from decimal import Decimal

from django.test import TestCase
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from apps.departments.models import Department
from apps.faculties.models import Faculty
from apps.kpi.models import KPI, KPIValue, PeriodType
from apps.kpi.services import (
    calculate_department_kpi,
    calculate_faculty_kpi,
    calculate_university_kpi,
)
from apps.users.models import Role, User


def _create_teacher_with_value(email, department, kpi, value, period_value="2026-04"):
    from apps.kpi.services import upsert_kpi_result

    teacher = User.objects.create_user(
        email=email, password="p", role=Role.TEACHER, department=department
    )
    KPIValue.objects.create(
        user=teacher,
        kpi=kpi,
        value=Decimal(value),
        period_type=PeriodType.MONTH,
        period_value=period_value,
    )
    upsert_kpi_result(teacher.id, PeriodType.MONTH, period_value)
    return teacher


class DepartmentKPIServiceTests(TestCase):
    def setUp(self):
        self.faculty = Faculty.objects.create(name="Инженерный")
        self.dept = Department.objects.create(name="ИТ", faculty=self.faculty)
        self.kpi = KPI.objects.create(name="A", weight=Decimal("0.5"))

    def test_no_teachers_returns_none(self):
        self.assertIsNone(
            calculate_department_kpi(self.dept.id, "month", "2026-04")
        )

    def test_inactive_teachers_not_counted(self):
        User.objects.create_user(
            email="t1@oshsu.kg",
            password="p",
            role=Role.TEACHER,
            department=self.dept,
            is_active=False,
        )
        self.assertIsNone(
            calculate_department_kpi(self.dept.id, "month", "2026-04")
        )

    def test_mean_of_teacher_kpis(self):
        _create_teacher_with_value("t1@oshsu.kg", self.dept, self.kpi, 80)
        _create_teacher_with_value("t2@oshsu.kg", self.dept, self.kpi, 40)
        # t1 = 80 × 0.5 = 40.00; t2 = 40 × 0.5 = 20.00; mean = 30.00
        result = calculate_department_kpi(self.dept.id, "month", "2026-04")
        self.assertEqual(result, Decimal("30.00"))


class FacultyKPIServiceTests(TestCase):
    def setUp(self):
        self.faculty = Faculty.objects.create(name="Ф")
        self.dept_a = Department.objects.create(name="A", faculty=self.faculty)
        self.dept_b = Department.objects.create(name="B", faculty=self.faculty)
        self.kpi = KPI.objects.create(name="KPI", weight=Decimal("0.5"))

    def test_no_departments_returns_none(self):
        empty = Faculty.objects.create(name="Empty")
        self.assertIsNone(calculate_faculty_kpi(empty.id, "month", "2026-04"))

    def test_all_departments_empty_returns_none(self):
        self.assertIsNone(
            calculate_faculty_kpi(self.faculty.id, "month", "2026-04")
        )

    def test_mean_of_department_kpis(self):
        _create_teacher_with_value("a@oshsu.kg", self.dept_a, self.kpi, 80)
        _create_teacher_with_value("b@oshsu.kg", self.dept_b, self.kpi, 40)
        # dept_a = 40.00, dept_b = 20.00, mean = 30.00
        result = calculate_faculty_kpi(self.faculty.id, "month", "2026-04")
        self.assertEqual(result, Decimal("30.00"))

    def test_empty_department_excluded_from_mean(self):
        _create_teacher_with_value("a@oshsu.kg", self.dept_a, self.kpi, 80)
        # dept_b empty → excluded → faculty = dept_a = 40.00
        result = calculate_faculty_kpi(self.faculty.id, "month", "2026-04")
        self.assertEqual(result, Decimal("40.00"))


class UniversityKPIServiceTests(TestCase):
    def test_no_active_faculties_returns_none(self):
        self.assertIsNone(calculate_university_kpi("month", "2026-04"))

    def test_mean_of_active_faculties(self):
        fac_a = Faculty.objects.create(name="A", is_active=True)
        fac_b = Faculty.objects.create(name="B", is_active=True)
        dept_a = Department.objects.create(name="DA", faculty=fac_a)
        dept_b = Department.objects.create(name="DB", faculty=fac_b)
        kpi = KPI.objects.create(name="KPI", weight=Decimal("0.5"))
        _create_teacher_with_value("a@oshsu.kg", dept_a, kpi, 80)
        _create_teacher_with_value("b@oshsu.kg", dept_b, kpi, 40)
        # fac_a = 40, fac_b = 20, uni = 30
        result = calculate_university_kpi("month", "2026-04")
        self.assertEqual(result, Decimal("30.00"))


class _AuthMixin:
    def _auth(self, user):
        token = RefreshToken.for_user(user).access_token
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")


class DepartmentKPIResultViewTests(_AuthMixin, APITestCase):
    def setUp(self):
        self.dean = User.objects.create_user(
            email="dean@oshsu.kg", password="p", role=Role.DEAN
        )
        self.teacher = User.objects.create_user(
            email="t@oshsu.kg", password="p", role=Role.TEACHER
        )
        self.faculty = Faculty.objects.create(name="Ф")
        self.dept = Department.objects.create(name="Д", faculty=self.faculty)

    def test_unauthenticated_returns_401(self):
        res = self.client.get(f"/api/kpi/result/department/{self.dept.id}/")
        self.assertEqual(res.status_code, 401)

    def test_teacher_forbidden(self):
        self._auth(self.teacher)
        res = self.client.get(f"/api/kpi/result/department/{self.dept.id}/")
        self.assertEqual(res.status_code, 403)

    def test_dean_can_read(self):
        self._auth(self.dean)
        res = self.client.get(f"/api/kpi/result/department/{self.dept.id}/")
        self.assertEqual(res.status_code, 200)
        self.assertIsNone(res.data["total_value"])


class FacultyKPIResultViewTests(_AuthMixin, APITestCase):
    def setUp(self):
        self.rector = User.objects.create_user(
            email="rector@oshsu.kg", password="p", role=Role.RECTOR
        )
        self.head = User.objects.create_user(
            email="head@oshsu.kg", password="p", role=Role.HEAD_OF_DEPT
        )
        self.faculty = Faculty.objects.create(name="Ф")

    def test_head_of_dept_forbidden(self):
        self._auth(self.head)
        res = self.client.get(f"/api/kpi/result/faculty/{self.faculty.id}/")
        self.assertEqual(res.status_code, 403)

    def test_rector_can_read(self):
        self._auth(self.rector)
        res = self.client.get(f"/api/kpi/result/faculty/{self.faculty.id}/")
        self.assertEqual(res.status_code, 200)


class UniversityKPIResultViewTests(_AuthMixin, APITestCase):
    def setUp(self):
        self.rector = User.objects.create_user(
            email="rector@oshsu.kg", password="p", role=Role.RECTOR
        )
        self.dean = User.objects.create_user(
            email="dean@oshsu.kg", password="p", role=Role.DEAN
        )

    def test_dean_forbidden(self):
        self._auth(self.dean)
        res = self.client.get("/api/kpi/result/university/")
        self.assertEqual(res.status_code, 403)

    def test_rector_can_read(self):
        self._auth(self.rector)
        res = self.client.get("/api/kpi/result/university/")
        self.assertEqual(res.status_code, 200)
