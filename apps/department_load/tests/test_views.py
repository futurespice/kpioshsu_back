from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from apps.departments.models import Department
from apps.department_load.models import DeptLoad
from apps.faculties.models import Faculty
from apps.users.models import Role, User


class _AuthMixin:
    def _auth(self, user):
        token = RefreshToken.for_user(user).access_token
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")


class DeptLoadTests(_AuthMixin, APITestCase):
    url = "/api/load/departments/"

    def setUp(self):
        self.admin = User.objects.create_user(
            email="admin@oshsu.kg", password="p", role=Role.ADMIN
        )
        self.vice = User.objects.create_user(
            email="vice@oshsu.kg", password="p", role=Role.VICE_RECTOR
        )
        self.dean = User.objects.create_user(
            email="dean@oshsu.kg", password="p", role=Role.DEAN
        )
        self.head = User.objects.create_user(
            email="head@oshsu.kg", password="p", role=Role.HEAD_OF_DEPT
        )
        self.teacher = User.objects.create_user(
            email="t@oshsu.kg", password="p", role=Role.TEACHER
        )
        self.faculty = Faculty.objects.create(name="F")
        self.dept = Department.objects.create(name="ИТ", faculty=self.faculty)
        self.load = DeptLoad.objects.create(
            department=self.dept,
            academic_year="2025-2026",
            semester=1,
            target_hours=1000,
            actual_hours=750,
        )

    def test_teacher_cannot_list(self):
        self._auth(self.teacher)
        self.assertEqual(self.client.get(self.url).status_code, 403)

    def test_vice_rector_sees_all(self):
        self._auth(self.vice)
        res = self.client.get(self.url)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data["count"], 1)
        self.assertEqual(res.data["result"][0]["pct"], "75.00")

    def test_dean_can_retrieve(self):
        self._auth(self.dean)
        res = self.client.get(f"{self.url}{self.load.id}/")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data["pct"], "75.00")

    def test_teacher_cannot_retrieve(self):
        self._auth(self.teacher)
        res = self.client.get(f"{self.url}{self.load.id}/")
        self.assertEqual(res.status_code, 403)

    def test_admin_can_create(self):
        self._auth(self.admin)
        other_dept = Department.objects.create(name="МАТ", faculty=self.faculty)
        res = self.client.post(
            self.url,
            {
                "department": str(other_dept.id),
                "academic_year": "2025-2026",
                "semester": 2,
                "target_hours": 500,
                "actual_hours": 100,
            },
            format="json",
        )
        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.data["pct"], "20.00")

    def test_semester_out_of_range_returns_422(self):
        self._auth(self.admin)
        other_dept = Department.objects.create(name="ФИЗ", faculty=self.faculty)
        res = self.client.post(
            self.url,
            {
                "department": str(other_dept.id),
                "academic_year": "2025-2026",
                "semester": 3,
                "target_hours": 500,
            },
            format="json",
        )
        self.assertEqual(res.status_code, 422)

    def test_head_of_dept_can_update(self):
        self._auth(self.head)
        res = self.client.patch(
            f"{self.url}{self.load.id}/",
            {"actual_hours": 1000},
            format="json",
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data["pct"], "100.00")

    def test_teacher_cannot_update(self):
        self._auth(self.teacher)
        res = self.client.patch(
            f"{self.url}{self.load.id}/",
            {"actual_hours": 1},
            format="json",
        )
        self.assertEqual(res.status_code, 403)

    def test_pct_zero_when_target_zero(self):
        zero_load = DeptLoad.objects.create(
            department=Department.objects.create(name="X", faculty=self.faculty),
            academic_year="2025-2026",
            semester=1,
            target_hours=0,
            actual_hours=100,
        )
        self._auth(self.vice)
        res = self.client.get(f"{self.url}{zero_load.id}/")
        self.assertEqual(res.data["pct"], "0.00")
