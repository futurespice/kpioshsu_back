from datetime import date

from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from apps.planerka.models import Planerka
from apps.users.models import Role, User


class _AuthMixin:
    def _auth(self, user):
        token = RefreshToken.for_user(user).access_token
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")


class PlanerkaTests(_AuthMixin, APITestCase):
    url = "/api/planerka/"

    def setUp(self):
        self.rector = User.objects.create_user(
            email="r@oshsu.kg", password="p", role=Role.RECTOR
        )
        self.vice = User.objects.create_user(
            email="v@oshsu.kg", password="p", role=Role.VICE_RECTOR
        )
        self.teacher = User.objects.create_user(
            email="t@oshsu.kg", password="p", role=Role.TEACHER
        )
        self.payload = {
            "title": "Совещание",
            "priority": "high",
            "deadline": "2026-06-01",
            "status": "scheduled",
        }

    def test_unauthenticated_list_returns_401(self):
        self.assertEqual(self.client.get(self.url).status_code, 401)

    def test_teacher_cannot_list(self):
        self._auth(self.teacher)
        self.assertEqual(self.client.get(self.url).status_code, 403)

    def test_rector_can_list(self):
        self._auth(self.rector)
        self.assertEqual(self.client.get(self.url).status_code, 200)

    def test_rector_cannot_create(self):
        self._auth(self.rector)
        res = self.client.post(self.url, self.payload, format="json")
        self.assertEqual(res.status_code, 403)

    def test_vice_rector_can_create(self):
        self._auth(self.vice)
        res = self.client.post(self.url, self.payload, format="json")
        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.data["created_by"], self.vice.id)

    def test_missing_title_returns_422(self):
        self._auth(self.vice)
        bad = {**self.payload}
        bad.pop("title")
        res = self.client.post(self.url, bad, format="json")
        self.assertEqual(res.status_code, 422)

    def test_invalid_priority_returns_422(self):
        self._auth(self.vice)
        bad = {**self.payload, "priority": "urgent"}
        res = self.client.post(self.url, bad, format="json")
        self.assertEqual(res.status_code, 422)

    def test_vice_rector_delete_is_soft(self):
        obj = Planerka.objects.create(
            title="T", priority="high", deadline=date(2026, 6, 1),
            status="scheduled", created_by=self.vice,
        )
        self._auth(self.vice)
        res = self.client.delete(f"{self.url}{obj.id}/")
        self.assertEqual(res.status_code, 204)
        self.assertTrue(Planerka.all_objects.filter(id=obj.id).exists())
        self.assertFalse(Planerka.objects.filter(id=obj.id).exists())

    def test_teacher_cannot_delete(self):
        obj = Planerka.objects.create(
            title="T", priority="high", deadline=date(2026, 6, 1),
            status="scheduled", created_by=self.vice,
        )
        self._auth(self.teacher)
        res = self.client.delete(f"{self.url}{obj.id}/")
        self.assertEqual(res.status_code, 403)
