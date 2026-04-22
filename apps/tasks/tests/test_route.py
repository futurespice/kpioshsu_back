from datetime import timedelta

from django.utils import timezone
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from apps.tasks.models import Priority, Task, TaskStatus
from apps.users.models import Role, User


class TaskRouteTests(APITestCase):
    def setUp(self):
        self.rector = User.objects.create_user(
            email="rector@oshsu.kg", password="p", role=Role.RECTOR
        )
        self.vice_rector = User.objects.create_user(
            email="vice@oshsu.kg", password="p", role=Role.VICE_RECTOR
        )
        self.dean = User.objects.create_user(
            email="dean@oshsu.kg", password="p", role=Role.DEAN
        )
        tomorrow = (timezone.now() + timedelta(days=1)).date()
        self.task = Task.objects.create(
            title="Стратегическая",
            priority=Priority.HIGH,
            points=50,
            deadline=tomorrow,
            from_user=self.rector,
            to_user=self.vice_rector,
        )
        self.url = f"/api/tasks/{self.task.id}/route/"

    def _auth(self, user):
        token = RefreshToken.for_user(user).access_token
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    def test_unauthenticated_returns_401(self):
        res = self.client.patch(
            self.url, {"destination": "Декан ИТ"}, format="json"
        )
        self.assertEqual(res.status_code, 401)

    def test_dean_cannot_route(self):
        self._auth(self.dean)
        res = self.client.patch(
            self.url, {"destination": "Декан ИТ"}, format="json"
        )
        self.assertEqual(res.status_code, 403)

    def test_vice_rector_can_route(self):
        self._auth(self.vice_rector)
        res = self.client.patch(
            self.url, {"destination": "Декан ИТ"}, format="json"
        )
        self.assertEqual(res.status_code, 200)
        self.task.refresh_from_db()
        self.assertEqual(self.task.status, TaskStatus.ROUTED)
        self.assertEqual(self.task.routed_to, "Декан ИТ")
        self.assertIsNotNone(self.task.routed_at)

    def test_missing_destination_returns_422(self):
        self._auth(self.vice_rector)
        res = self.client.patch(self.url, {}, format="json")
        self.assertEqual(res.status_code, 422)
