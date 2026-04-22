from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from apps.notifications.models import Notification, NotificationType
from apps.users.models import Role, User


class _AuthMixin:
    def _auth(self, user):
        token = RefreshToken.for_user(user).access_token
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")


class NotificationTests(_AuthMixin, APITestCase):
    url = "/api/notifications/"

    def setUp(self):
        self.admin = User.objects.create_user(
            email="a@oshsu.kg", password="p", role=Role.ADMIN
        )
        self.alice = User.objects.create_user(
            email="alice@oshsu.kg", password="p", role=Role.TEACHER
        )
        self.bob = User.objects.create_user(
            email="bob@oshsu.kg", password="p", role=Role.TEACHER
        )
        self.alice_notif = Notification.objects.create(
            user=self.alice, type=NotificationType.INFO, title="Hi alice"
        )
        self.bob_notif = Notification.objects.create(
            user=self.bob, type=NotificationType.ALERT, title="Hi bob"
        )

    def test_unauthenticated_returns_401(self):
        self.assertEqual(self.client.get(self.url).status_code, 401)

    def test_list_scoped_to_self(self):
        self._auth(self.alice)
        res = self.client.get(self.url)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data["count"], 1)
        self.assertEqual(res.data["result"][0]["id"], str(self.alice_notif.id))

    def test_cannot_retrieve_other_users_notification(self):
        self._auth(self.alice)
        res = self.client.get(f"{self.url}{self.bob_notif.id}/")
        self.assertEqual(res.status_code, 404)

    def test_teacher_cannot_create(self):
        self._auth(self.alice)
        res = self.client.post(
            self.url,
            {
                "user": str(self.alice.id),
                "type": NotificationType.INFO,
                "title": "x",
            },
            format="json",
        )
        self.assertEqual(res.status_code, 403)

    def test_admin_can_create_for_user(self):
        self._auth(self.admin)
        res = self.client.post(
            self.url,
            {
                "user": str(self.alice.id),
                "type": NotificationType.DEADLINE,
                "title": "Срок задачи",
                "message": "Завтра дедлайн",
            },
            format="json",
        )
        self.assertEqual(res.status_code, 201)

    def test_mark_read(self):
        self._auth(self.alice)
        res = self.client.patch(f"{self.url}{self.alice_notif.id}/read/")
        self.assertEqual(res.status_code, 200)
        self.alice_notif.refresh_from_db()
        self.assertTrue(self.alice_notif.is_read)

    def test_cannot_mark_others_as_read(self):
        self._auth(self.alice)
        res = self.client.patch(f"{self.url}{self.bob_notif.id}/read/")
        self.assertEqual(res.status_code, 404)

    def test_unread_count(self):
        Notification.objects.create(
            user=self.alice, type=NotificationType.ALERT, title="X", is_read=True
        )
        Notification.objects.create(
            user=self.alice, type=NotificationType.ALERT, title="Y"
        )
        self._auth(self.alice)
        res = self.client.get(f"{self.url}unread-count/")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data["count"], 2)

    def test_delete_is_soft(self):
        self._auth(self.alice)
        res = self.client.delete(f"{self.url}{self.alice_notif.id}/")
        self.assertEqual(res.status_code, 204)
        self.assertTrue(Notification.all_objects.filter(id=self.alice_notif.id).exists())
        self.assertFalse(Notification.objects.filter(id=self.alice_notif.id).exists())
