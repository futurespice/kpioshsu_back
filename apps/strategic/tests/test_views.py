from decimal import Decimal

from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from apps.faculties.models import Faculty
from apps.strategic.models import (
    Grant,
    GrantStatus,
    Program,
    ProgramStatus,
    StrategicGoal,
)
from apps.users.models import Role, User


class _AuthMixin:
    def _auth(self, user):
        token = RefreshToken.for_user(user).access_token
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")


class StrategicGoalTests(_AuthMixin, APITestCase):
    url = "/api/strategic-goals/"

    def setUp(self):
        self.admin = User.objects.create_user(
            email="admin@oshsu.kg", password="p", role=Role.ADMIN
        )
        self.rector = User.objects.create_user(
            email="r@oshsu.kg", password="p", role=Role.RECTOR
        )
        self.vice = User.objects.create_user(
            email="v@oshsu.kg", password="p", role=Role.VICE_RECTOR
        )
        self.teacher = User.objects.create_user(
            email="t@oshsu.kg", password="p", role=Role.TEACHER
        )

    def test_teacher_cannot_list(self):
        self._auth(self.teacher)
        self.assertEqual(self.client.get(self.url).status_code, 403)

    def test_rector_can_list(self):
        StrategicGoal.objects.create(
            title="Публикаций в Scopus до 120",
            current_value=Decimal("89"),
            target_value=Decimal("120"),
            unit="ед.",
            academic_year="2025-2026",
        )
        self._auth(self.rector)
        res = self.client.get(self.url)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data["count"], 1)

    def test_filter_by_year(self):
        StrategicGoal.objects.create(
            title="A", current_value=Decimal("1"), target_value=Decimal("10"),
            academic_year="2024-2025",
        )
        StrategicGoal.objects.create(
            title="B", current_value=Decimal("2"), target_value=Decimal("20"),
            academic_year="2025-2026",
        )
        self._auth(self.vice)
        res = self.client.get(self.url, {"year": "2025-2026"})
        self.assertEqual(res.data["count"], 1)

    def test_admin_can_create(self):
        self._auth(self.admin)
        res = self.client.post(
            self.url,
            {
                "title": "X",
                "current_value": "10",
                "target_value": "100",
                "academic_year": "2025-2026",
            },
            format="json",
        )
        self.assertEqual(res.status_code, 201)

    def test_rector_can_update_current_value(self):
        g = StrategicGoal.objects.create(
            title="G", current_value=Decimal("10"), target_value=Decimal("100"),
            academic_year="2025-2026",
        )
        self._auth(self.rector)
        res = self.client.patch(
            f"{self.url}{g.id}/", {"current_value": "50"}, format="json"
        )
        self.assertEqual(res.status_code, 200)

    def test_vice_cannot_update(self):
        g = StrategicGoal.objects.create(
            title="G", current_value=Decimal("10"), target_value=Decimal("100"),
            academic_year="2025-2026",
        )
        self._auth(self.vice)
        res = self.client.patch(
            f"{self.url}{g.id}/", {"current_value": "50"}, format="json"
        )
        self.assertEqual(res.status_code, 403)


class GrantTests(_AuthMixin, APITestCase):
    url = "/api/grants/"

    def setUp(self):
        self.admin = User.objects.create_user(
            email="admin@oshsu.kg", password="p", role=Role.ADMIN
        )
        self.rector = User.objects.create_user(
            email="r@oshsu.kg", password="p", role=Role.RECTOR
        )
        self.teacher = User.objects.create_user(
            email="t@oshsu.kg", password="p", role=Role.TEACHER
        )
        Grant.objects.create(
            title="Ф1", amount=Decimal("100000"), status=GrantStatus.ACTIVE, year=2025
        )
        Grant.objects.create(
            title="Ф2", amount=Decimal("50000"), status=GrantStatus.COMPLETED, year=2024
        )

    def test_teacher_cannot_list(self):
        self._auth(self.teacher)
        self.assertEqual(self.client.get(self.url).status_code, 403)

    def test_rector_can_list(self):
        self._auth(self.rector)
        res = self.client.get(self.url)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data["count"], 2)

    def test_filter_by_status(self):
        self._auth(self.rector)
        res = self.client.get(self.url, {"status": "active"})
        self.assertEqual(res.data["count"], 1)


class ProgramTests(_AuthMixin, APITestCase):
    url = "/api/programs/"

    def setUp(self):
        self.admin = User.objects.create_user(
            email="admin@oshsu.kg", password="p", role=Role.ADMIN
        )
        self.teacher = User.objects.create_user(
            email="t@oshsu.kg", password="p", role=Role.TEACHER
        )
        self.faculty = Faculty.objects.create(name="Инж")
        Program.objects.create(
            title="ИТ", faculty=self.faculty, status=ProgramStatus.ACCREDITED
        )

    def test_teacher_can_list(self):
        self._auth(self.teacher)
        self.assertEqual(self.client.get(self.url).status_code, 200)

    def test_filter_by_faculty(self):
        self._auth(self.teacher)
        res = self.client.get(self.url, {"faculty_id": str(self.faculty.id)})
        self.assertEqual(res.data["count"], 1)

    def test_teacher_cannot_create(self):
        self._auth(self.teacher)
        res = self.client.post(
            self.url,
            {
                "title": "X",
                "faculty": str(self.faculty.id),
                "status": ProgramStatus.ACCREDITED,
            },
            format="json",
        )
        self.assertEqual(res.status_code, 403)

    def test_admin_can_create(self):
        self._auth(self.admin)
        res = self.client.post(
            self.url,
            {
                "title": "X",
                "faculty": str(self.faculty.id),
                "status": ProgramStatus.ACCREDITED,
            },
            format="json",
        )
        self.assertEqual(res.status_code, 201)


class AnalyticsOverviewWithStrategicTests(_AuthMixin, APITestCase):
    url = "/api/analytics/university/overview/"

    def setUp(self):
        self.rector = User.objects.create_user(
            email="r@oshsu.kg", password="p", role=Role.RECTOR
        )
        faculty = Faculty.objects.create(name="F")
        Grant.objects.create(
            title="A", amount=Decimal("1"), status=GrantStatus.ACTIVE, year=2025
        )
        Grant.objects.create(
            title="B", amount=Decimal("1"), status=GrantStatus.COMPLETED, year=2025
        )
        Program.objects.create(
            title="P", faculty=faculty, status=ProgramStatus.ACCREDITED
        )

    def test_overview_counts_grants_and_programs(self):
        self._auth(self.rector)
        res = self.client.get(self.url)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data["grants_count"], 1)
        self.assertEqual(res.data["programs_count"], 1)


class UniversityGoalsReadsStrategicTests(_AuthMixin, APITestCase):
    url = "/api/analytics/university/goals/"

    def setUp(self):
        self.rector = User.objects.create_user(
            email="r@oshsu.kg", password="p", role=Role.RECTOR
        )
        StrategicGoal.objects.create(
            title="Active", current_value=Decimal("10"),
            target_value=Decimal("100"), academic_year="2025-2026",
            is_active=True,
        )
        StrategicGoal.objects.create(
            title="Inactive", current_value=Decimal("1"),
            target_value=Decimal("10"), academic_year="2025-2026",
            is_active=False,
        )

    def test_returns_active_goals_only(self):
        self._auth(self.rector)
        res = self.client.get(self.url)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]["title"], "Active")
