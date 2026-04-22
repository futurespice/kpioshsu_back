from decimal import Decimal

from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from apps.departments.models import Department
from apps.faculties.models import Faculty
from apps.kpi.models import KPI, KPIValue, PeriodType
from apps.publications.models import JournalType, Publication
from apps.users.models import Role, User


class _AuthMixin:
    def _auth(self, user):
        token = RefreshToken.for_user(user).access_token
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")


class DeanAnalyticsTests(_AuthMixin, APITestCase):
    def setUp(self):
        self.faculty = Faculty.objects.create(name="Инж")
        self.other_faculty = Faculty.objects.create(name="Гум")
        self.dean = User.objects.create_user(
            email="dean@oshsu.kg", password="p", role=Role.DEAN,
            faculty=self.faculty,
        )
        self.teacher_from = User.objects.create_user(
            email="tf@oshsu.kg", password="p", role=Role.TEACHER,
            faculty=self.faculty, full_name="Тестовый",
        )
        self.dept = Department.objects.create(
            name="ИТ", faculty=self.faculty, target_hours=800
        )
        self.teacher_from.department = self.dept
        self.teacher_from.save()
        # Teacher in another faculty — должен исключаться
        User.objects.create_user(
            email="to@oshsu.kg", password="p", role=Role.TEACHER,
            faculty=self.other_faculty,
        )
        self.rector = User.objects.create_user(
            email="r@oshsu.kg", password="p", role=Role.RECTOR
        )

    def test_teacher_forbidden_overview(self):
        self._auth(self.teacher_from)
        self.assertEqual(
            self.client.get("/api/analytics/dean/overview/").status_code, 403
        )

    def test_dean_overview_scoped_to_faculty(self):
        self._auth(self.dean)
        res = self.client.get("/api/analytics/dean/overview/")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data["faculty_id"], str(self.faculty.id))
        self.assertEqual(res.data["departments_count"], 1)
        self.assertEqual(res.data["teachers_count"], 1)

    def test_dean_teachers_only_from_faculty(self):
        Publication.objects.create(
            user=self.teacher_from, title="A",
            journal_type=JournalType.SCOPUS,
            pub_date="2025-10-01", academic_year="2025-2026",
        )
        self._auth(self.dean)
        res = self.client.get("/api/analytics/dean/teachers/")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.data), 1)
        t = res.data[0]
        self.assertEqual(t["full_name"], "Тестовый")
        self.assertEqual(t["department"], "ИТ")
        self.assertEqual(t["publications_count"], 1)

    def test_dean_teachers_computes_kpi(self):
        from apps.kpi.services import upsert_kpi_result

        kpi = KPI.objects.create(name="K", weight=Decimal("0.5"))
        KPIValue.objects.create(
            user=self.teacher_from, kpi=kpi, value=Decimal(80),
            period_type=PeriodType.MONTH, period_value="2026-04",
        )
        upsert_kpi_result(self.teacher_from.id, PeriodType.MONTH, "2026-04")
        self._auth(self.dean)
        res = self.client.get(
            "/api/analytics/dean/teachers/",
            {"period_type": "month", "period_value": "2026-04"},
        )
        # Формула ТЗ v2: 80 × 0.5 = 40.00
        self.assertEqual(res.data[0]["kpi"], "40.00")

    def test_dean_departments_scoped(self):
        self._auth(self.dean)
        res = self.client.get("/api/analytics/dean/departments/")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.data), 1)
        d = res.data[0]
        self.assertEqual(d["name"], "ИТ")
        self.assertEqual(d["target_hours"], 800)
        self.assertEqual(d["teachers_count"], 1)

    def test_admin_can_use_faculty_id_param(self):
        admin = User.objects.create_user(
            email="admin@oshsu.kg", password="p", role=Role.ADMIN
        )
        self._auth(admin)
        res = self.client.get(
            "/api/analytics/dean/overview/",
            {"faculty_id": str(self.faculty.id)},
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data["faculty_id"], str(self.faculty.id))
        self.assertEqual(res.data["departments_count"], 1)

    def test_rector_forbidden(self):
        self._auth(self.rector)
        self.assertEqual(
            self.client.get("/api/analytics/dean/overview/").status_code, 403
        )
