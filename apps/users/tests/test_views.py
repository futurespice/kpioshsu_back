from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from apps.departments.models import Department
from apps.faculties.models import Faculty
from apps.users.models import Role, User


class _AuthMixin:
    def _auth(self, user):
        token = RefreshToken.for_user(user).access_token
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")


class UserViewSetTests(_AuthMixin, APITestCase):
    url = "/api/users/"

    def setUp(self):
        self.admin = User.objects.create_user(
            email="admin@oshsu.kg", password="p", role=Role.ADMIN
        )
        self.dean = User.objects.create_user(
            email="dean@oshsu.kg", password="p", role=Role.DEAN
        )
        self.teacher = User.objects.create_user(
            email="teacher@oshsu.kg",
            password="p",
            role=Role.TEACHER,
            full_name="Тестовый Препод",
        )
        self.faculty = Faculty.objects.create(name="Инженерный")
        self.dept = Department.objects.create(name="ИТ", faculty=self.faculty)

    def test_unauthenticated_list_returns_401(self):
        res = self.client.get(self.url)
        self.assertEqual(res.status_code, 401)

    def test_teacher_cannot_list(self):
        self._auth(self.teacher)
        res = self.client.get(self.url)
        self.assertEqual(res.status_code, 403)

    def test_dean_can_list(self):
        self._auth(self.dean)
        res = self.client.get(self.url)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data["count"], 3)

    def test_password_not_in_list(self):
        self._auth(self.dean)
        res = self.client.get(self.url)
        self.assertNotIn("password", res.data["result"][0])

    def test_teacher_can_retrieve(self):
        self._auth(self.teacher)
        res = self.client.get(f"{self.url}{self.admin.id}/")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data["email"], "admin@oshsu.kg")

    def test_filter_by_role(self):
        self._auth(self.dean)
        res = self.client.get(self.url, {"role": Role.TEACHER.value})
        self.assertEqual(res.data["count"], 1)
        self.assertEqual(res.data["result"][0]["id"], str(self.teacher.id))

    def test_filter_by_dept_id(self):
        self.teacher.department = self.dept
        self.teacher.save()
        self._auth(self.dean)
        res = self.client.get(self.url, {"dept_id": str(self.dept.id)})
        self.assertEqual(res.data["count"], 1)

    def test_teacher_cannot_create(self):
        self._auth(self.teacher)
        res = self.client.post(
            self.url,
            {"email": "new@oshsu.kg", "password": "p", "role": Role.TEACHER.value},
            format="json",
        )
        self.assertEqual(res.status_code, 403)

    def test_admin_can_create(self):
        self._auth(self.admin)
        res = self.client.post(
            self.url,
            {
                "email": "new@oshsu.kg",
                "password": "p",
                "role": Role.TEACHER.value,
                "full_name": "Новый",
            },
            format="json",
        )
        self.assertEqual(res.status_code, 201)
        user = User.objects.get(email="new@oshsu.kg")
        self.assertTrue(user.check_password("p"))
        self.assertNotIn("password", res.data)

    def test_admin_create_with_bad_email_returns_422(self):
        self._auth(self.admin)
        res = self.client.post(
            self.url,
            {"email": "bad@gmail.com", "password": "p", "role": Role.TEACHER.value},
            format="json",
        )
        self.assertEqual(res.status_code, 422)

    def test_admin_can_update_password(self):
        self._auth(self.admin)
        res = self.client.patch(
            f"{self.url}{self.teacher.id}/",
            {"password": "newsecret"},
            format="json",
        )
        self.assertEqual(res.status_code, 200)
        self.teacher.refresh_from_db()
        self.assertTrue(self.teacher.check_password("newsecret"))

    def test_admin_delete_is_soft(self):
        self._auth(self.admin)
        res = self.client.delete(f"{self.url}{self.teacher.id}/")
        self.assertEqual(res.status_code, 204)
        self.assertTrue(User.all_objects.filter(id=self.teacher.id).exists())
        self.assertFalse(User.objects.filter(id=self.teacher.id).exists())

    def test_dean_cannot_delete(self):
        self._auth(self.dean)
        res = self.client.delete(f"{self.url}{self.teacher.id}/")
        self.assertEqual(res.status_code, 403)
