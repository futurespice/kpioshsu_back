from decimal import Decimal

from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from apps.approvals.models import Approval, ApprovalStatus, ApprovalType
from apps.departments.models import Department
from apps.documents.models import Document, DocType, DocumentStatus
from apps.faculties.models import Faculty
from apps.kpi.models import KPI, KPIValue, PeriodType
from apps.publications.models import JournalType, Publication
from apps.users.models import Role, User


class _AuthMixin:
    def _auth(self, user):
        token = RefreshToken.for_user(user).access_token
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")


class UniversityOverviewTests(_AuthMixin, APITestCase):
    url = "/api/analytics/university/overview/"

    def setUp(self):
        self.rector = User.objects.create_user(
            email="rector@oshsu.kg", password="p", role=Role.RECTOR
        )
        self.teacher = User.objects.create_user(
            email="t1@oshsu.kg", password="p", role=Role.TEACHER
        )

    def test_teacher_forbidden(self):
        self._auth(self.teacher)
        self.assertEqual(self.client.get(self.url).status_code, 403)

    def test_rector_returns_counts(self):
        Publication.objects.create(
            user=self.teacher, title="A",
            journal_type=JournalType.SCOPUS,
            pub_date="2025-10-01", academic_year="2025-2026",
        )
        self._auth(self.rector)
        res = self.client.get(self.url)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data["teachers_count"], 1)
        self.assertEqual(res.data["publications_count"], 1)
        self.assertEqual(res.data["grants_count"], 0)


class UniversityFacultyKpiTests(_AuthMixin, APITestCase):
    url = "/api/analytics/university/faculty-kpi/"

    def setUp(self):
        self.vice = User.objects.create_user(
            email="v@oshsu.kg", password="p", role=Role.VICE_RECTOR
        )
        Faculty.objects.create(name="A")
        Faculty.objects.create(name="B")

    def test_returns_list_of_faculties(self):
        self._auth(self.vice)
        res = self.client.get(self.url)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.data), 2)
        self.assertIn("name", res.data[0])
        self.assertIn("kpi", res.data[0])


class UniversityKpiTrendTests(_AuthMixin, APITestCase):
    url = "/api/analytics/university/kpi-trend/"

    def setUp(self):
        self.rector = User.objects.create_user(
            email="r@oshsu.kg", password="p", role=Role.RECTOR
        )
        fac = Faculty.objects.create(name="F", is_active=True)
        dept = Department.objects.create(name="D", faculty=fac)
        teacher = User.objects.create_user(
            email="t@oshsu.kg", password="p", role=Role.TEACHER, department=dept
        )
        kpi = KPI.objects.create(name="K", weight=Decimal("0.5"))
        for month in ["2025-10", "2025-11"]:
            KPIValue.objects.create(
                user=teacher, kpi=kpi, value=Decimal(80),
                period_type=PeriodType.MONTH, period_value=month,
            )

    def test_returns_periods(self):
        self._auth(self.rector)
        res = self.client.get(self.url)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.data), 2)
        periods = [row["period"] for row in res.data]
        self.assertEqual(periods, ["2025-10", "2025-11"])


class UniversityGoalsAlertsTests(_AuthMixin, APITestCase):
    def setUp(self):
        self.rector = User.objects.create_user(
            email="r@oshsu.kg", password="p", role=Role.RECTOR
        )
        self.vice = User.objects.create_user(
            email="v@oshsu.kg", password="p", role=Role.VICE_RECTOR
        )

    def test_vice_rector_forbidden_goals(self):
        self._auth(self.vice)
        res = self.client.get("/api/analytics/university/goals/")
        self.assertEqual(res.status_code, 403)

    def test_rector_goals_returns_list(self):
        self._auth(self.rector)
        res = self.client.get("/api/analytics/university/goals/")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data, [])

    def test_rector_alerts_returns_list(self):
        self._auth(self.rector)
        res = self.client.get("/api/analytics/university/alerts/")
        self.assertEqual(res.status_code, 200)


class UniversityRadarHeatmapTests(_AuthMixin, APITestCase):
    def setUp(self):
        self.vice = User.objects.create_user(
            email="v@oshsu.kg", password="p", role=Role.VICE_RECTOR
        )

    def test_radar_ok(self):
        self._auth(self.vice)
        res = self.client.get("/api/analytics/university/radar/")
        self.assertEqual(res.status_code, 200)

    def test_heatmap_ok(self):
        self._auth(self.vice)
        res = self.client.get("/api/analytics/university/heatmap/")
        self.assertEqual(res.status_code, 200)
        self.assertIn("periods", res.data)
        self.assertIn("rows", res.data)


class ViceRectorOverviewTests(_AuthMixin, APITestCase):
    url = "/api/analytics/vice-rector/overview/"

    def setUp(self):
        self.vice = User.objects.create_user(
            email="v@oshsu.kg", password="p", role=Role.VICE_RECTOR
        )
        self.rector = User.objects.create_user(
            email="r@oshsu.kg", password="p", role=Role.RECTOR
        )
        Approval.objects.create(
            type=ApprovalType.UMK, title="A",
            from_user=self.vice, status=ApprovalStatus.PENDING,
        )
        Approval.objects.create(
            type=ApprovalType.REPORT, title="B",
            from_user=self.vice, status=ApprovalStatus.APPROVED,
        )

    def test_rector_forbidden(self):
        # ТЗ: /vice-rector/* доступ только VICE_RECTOR
        self._auth(self.rector)
        self.assertEqual(self.client.get(self.url).status_code, 403)

    def test_vice_sees_counts(self):
        self._auth(self.vice)
        res = self.client.get(self.url)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data["approvals_pending"], 1)


class ViceRectorDeptLoadTests(_AuthMixin, APITestCase):
    url = "/api/analytics/vice-rector/dept-load/"

    def setUp(self):
        self.vice = User.objects.create_user(
            email="v@oshsu.kg", password="p", role=Role.VICE_RECTOR
        )
        self.faculty = Faculty.objects.create(name="F")
        self.dept = Department.objects.create(
            name="ИТ", faculty=self.faculty, target_hours=1000
        )

    def test_returns_load_with_pct(self):
        self._auth(self.vice)
        res = self.client.get(self.url)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.data), 1)
        row = res.data[0]
        self.assertEqual(row["dept"], "ИТ")
        self.assertEqual(row["target"], 1000)
        self.assertEqual(row["hours"], 0)
        self.assertEqual(row["pct"], 0)


class ViceRectorUmkStatusTests(_AuthMixin, APITestCase):
    url = "/api/analytics/vice-rector/umk-status/"

    def setUp(self):
        self.vice = User.objects.create_user(
            email="v@oshsu.kg", password="p", role=Role.VICE_RECTOR
        )
        teacher = User.objects.create_user(
            email="t@oshsu.kg", password="p", role=Role.TEACHER
        )
        faculty = Faculty.objects.create(name="F")
        dept = Department.objects.create(name="Д", faculty=faculty)
        Document.objects.create(
            title="УМК БД", doc_type=DocType.UMK, user=teacher,
            department=dept, file_path="/u", academic_year="2025-2026",
            status=DocumentStatus.APPROVED,
        )

    def test_returns_subject_dept_status(self):
        self._auth(self.vice)
        res = self.client.get(self.url)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]["subject"], "УМК БД")
        self.assertEqual(res.data[0]["dept"], "Д")
        self.assertEqual(res.data[0]["status"], "approved")
