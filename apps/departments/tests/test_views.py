from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from apps.departments.models import Department
from apps.faculties.models import Faculty
from apps.users.models import Role, User


class DepartmentViewSetTests(APITestCase):
    url = "/api/departments/"

    def setUp(self):
        self.admin = User.objects.create_user(
            email="admin@oshsu.kg", password="pass12345", role=Role.ADMIN
        )
        self.teacher = User.objects.create_user(
            email="teacher@oshsu.kg", password="pass12345", role=Role.TEACHER
        )
        self.faculty_a = Faculty.objects.create(name="Инженерный")
        self.faculty_b = Faculty.objects.create(name="Гуманитарный")
        self.dept_a = Department.objects.create(
            name="Кафедра информатики", short="ИТ", faculty=self.faculty_a
        )
        self.dept_b = Department.objects.create(
            name="Кафедра литературы", short="ЛИТ", faculty=self.faculty_b
        )

    def _auth(self, user):
        token = RefreshToken.for_user(user).access_token
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    def test_unauthenticated_returns_401(self):
        res = self.client.get(self.url)
        self.assertEqual(res.status_code, 401)

    def test_list_returns_all_for_authenticated(self):
        self._auth(self.teacher)
        res = self.client.get(self.url)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data["count"], 2)

    def test_filter_by_faculty_id(self):
        self._auth(self.teacher)
        res = self.client.get(self.url, {"faculty_id": str(self.faculty_a.id)})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data["count"], 1)
        self.assertEqual(res.data["result"][0]["id"], str(self.dept_a.id))

    def test_teacher_cannot_create(self):
        self._auth(self.teacher)
        res = self.client.post(
            self.url,
            {"name": "X", "faculty": str(self.faculty_a.id)},
            format="json",
        )
        self.assertEqual(res.status_code, 403)

    def test_admin_can_create(self):
        self._auth(self.admin)
        res = self.client.post(
            self.url,
            {
                "name": "Кафедра математики",
                "short": "МАТ",
                "faculty": str(self.faculty_a.id),
            },
            format="json",
        )
        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.data["name"], "Кафедра математики")

    def test_create_without_faculty_returns_422(self):
        self._auth(self.admin)
        res = self.client.post(self.url, {"name": "X"}, format="json")
        self.assertEqual(res.status_code, 422)

    def test_teacher_count_computed(self):
        User.objects.create_user(
            email="t1@oshsu.kg",
            password="pass12345",
            role=Role.TEACHER,
            department=self.dept_a,
        )
        User.objects.create_user(
            email="t2@oshsu.kg",
            password="pass12345",
            role=Role.TEACHER,
            department=self.dept_a,
            is_active=False,
        )
        self._auth(self.teacher)
        res = self.client.get(f"{self.url}{self.dept_a.id}/")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data["teacher_count"], 1)

    def test_admin_delete_is_soft(self):
        self._auth(self.admin)
        res = self.client.delete(f"{self.url}{self.dept_a.id}/")
        self.assertEqual(res.status_code, 204)
        self.assertTrue(Department.all_objects.filter(id=self.dept_a.id).exists())

    def test_soft_deleted_returns_404(self):
        self.dept_a.soft_delete()
        self._auth(self.teacher)
        res = self.client.get(f"{self.url}{self.dept_a.id}/")
        self.assertEqual(res.status_code, 404)
