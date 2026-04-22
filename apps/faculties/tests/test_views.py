from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from apps.faculties.models import Faculty
from apps.users.models import Role, User


class FacultyViewSetTests(APITestCase):
    url = "/api/faculties/"

    def setUp(self):
        self.admin = User.objects.create_user(
            email="admin@oshsu.kg", password="pass12345", role=Role.ADMIN
        )
        self.teacher = User.objects.create_user(
            email="teacher@oshsu.kg", password="pass12345", role=Role.TEACHER
        )
        self.faculty = Faculty.objects.create(name="Инженерный факультет")

    def _auth(self, user):
        token = RefreshToken.for_user(user).access_token
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    def test_unauthenticated_list_returns_401(self):
        res = self.client.get(self.url)
        self.assertEqual(res.status_code, 401)

    def test_authenticated_list_returns_200_with_pagination(self):
        self._auth(self.teacher)
        res = self.client.get(self.url)
        self.assertEqual(res.status_code, 200)
        self.assertIn("count", res.data)
        self.assertIn("result", res.data)
        self.assertNotIn("results", res.data)
        self.assertEqual(len(res.data["result"]), 1)

    def test_teacher_cannot_create(self):
        self._auth(self.teacher)
        res = self.client.post(self.url, {"name": "Новый"}, format="json")
        self.assertEqual(res.status_code, 403)

    def test_admin_can_create(self):
        self._auth(self.admin)
        res = self.client.post(
            self.url,
            {"name": "Гуманитарный", "short_name": "hum"},
            format="json",
        )
        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.data["name"], "Гуманитарный")

    def test_admin_invalid_payload_returns_422(self):
        self._auth(self.admin)
        res = self.client.post(self.url, {}, format="json")
        self.assertEqual(res.status_code, 422)

    def test_admin_can_update(self):
        self._auth(self.admin)
        res = self.client.patch(
            f"{self.url}{self.faculty.id}/",
            {"short_name": "eng"},
            format="json",
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data["short_name"], "eng")

    def test_admin_delete_is_soft(self):
        self._auth(self.admin)
        res = self.client.delete(f"{self.url}{self.faculty.id}/")
        self.assertEqual(res.status_code, 204)
        self.assertTrue(Faculty.all_objects.filter(id=self.faculty.id).exists())
        self.assertFalse(Faculty.objects.filter(id=self.faculty.id).exists())

    def test_soft_deleted_returns_404(self):
        self.faculty.soft_delete()
        self._auth(self.teacher)
        res = self.client.get(f"{self.url}{self.faculty.id}/")
        self.assertEqual(res.status_code, 404)
