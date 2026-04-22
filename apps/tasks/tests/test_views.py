from datetime import timedelta

from django.utils import timezone
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from apps.tasks.models import Priority, Task, TaskStatus
from apps.users.models import Role, User


class _AuthMixin:
    def _auth(self, user):
        token = RefreshToken.for_user(user).access_token
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")


class _BaseTaskTestCase(_AuthMixin, APITestCase):
    url = "/api/tasks/"

    def setUp(self):
        self.admin = User.objects.create_user(
            email="admin@oshsu.kg", password="p", role=Role.ADMIN
        )
        self.dean = User.objects.create_user(
            email="dean@oshsu.kg", password="p", role=Role.DEAN
        )
        self.head = User.objects.create_user(
            email="head@oshsu.kg", password="p", role=Role.HEAD_OF_DEPT
        )
        self.teacher = User.objects.create_user(
            email="teacher@oshsu.kg", password="p", role=Role.TEACHER
        )
        self.tomorrow = (timezone.now() + timedelta(days=1)).date()
        self.yesterday = (timezone.now() - timedelta(days=1)).date()
        self.valid_payload = {
            "title": "Подготовить отчёт",
            "priority": "high",
            "points": 10,
            "deadline": self.tomorrow.isoformat(),
            "to_user": str(self.teacher.id),
        }


class TaskCreateTests(_BaseTaskTestCase):
    def test_unauthenticated_returns_401(self):
        res = self.client.post(self.url, self.valid_payload, format="json")
        self.assertEqual(res.status_code, 401)

    def test_teacher_cannot_create(self):
        self._auth(self.teacher)
        res = self.client.post(self.url, self.valid_payload, format="json")
        self.assertEqual(res.status_code, 403)

    def test_head_of_dept_can_create(self):
        self._auth(self.head)
        res = self.client.post(self.url, self.valid_payload, format="json")
        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.data["from_user"], self.head.id)
        self.assertEqual(res.data["status"], TaskStatus.PENDING)

    def test_past_deadline_returns_422(self):
        self._auth(self.head)
        bad = {**self.valid_payload, "deadline": self.yesterday.isoformat()}
        res = self.client.post(self.url, bad, format="json")
        self.assertEqual(res.status_code, 422)

    def test_invalid_priority_returns_422(self):
        self._auth(self.head)
        bad = {**self.valid_payload, "priority": "urgent"}
        res = self.client.post(self.url, bad, format="json")
        self.assertEqual(res.status_code, 422)

    def test_missing_title_returns_422(self):
        self._auth(self.head)
        bad = {**self.valid_payload}
        bad.pop("title")
        res = self.client.post(self.url, bad, format="json")
        self.assertEqual(res.status_code, 422)


class TaskListFilterTests(_BaseTaskTestCase):
    def setUp(self):
        super().setUp()
        self.t1 = Task.objects.create(
            title="A", priority=Priority.HIGH, status=TaskStatus.PENDING,
            points=5, deadline=self.tomorrow, from_user=self.head,
            to_user=self.teacher,
        )
        self.t2 = Task.objects.create(
            title="B", priority=Priority.LOW, status=TaskStatus.COMPLETED,
            points=3, deadline=self.tomorrow, from_user=self.dean,
            to_user=self.teacher,
        )

    def test_unauthenticated_list_returns_401(self):
        res = self.client.get(self.url)
        self.assertEqual(res.status_code, 401)

    def test_list_returns_all(self):
        self._auth(self.teacher)
        res = self.client.get(self.url)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data["count"], 2)

    def test_filter_by_status(self):
        self._auth(self.teacher)
        res = self.client.get(self.url, {"status": "pending"})
        self.assertEqual(res.data["count"], 1)
        self.assertEqual(res.data["result"][0]["id"], str(self.t1.id))

    def test_filter_by_priority(self):
        self._auth(self.teacher)
        res = self.client.get(self.url, {"priority": "high"})
        self.assertEqual(res.data["count"], 1)

    def test_filter_by_from_user(self):
        self._auth(self.teacher)
        res = self.client.get(self.url, {"from_user": str(self.head.id)})
        self.assertEqual(res.data["count"], 1)
        self.assertEqual(res.data["result"][0]["id"], str(self.t1.id))


class TaskMyOutgoingTests(_BaseTaskTestCase):
    def setUp(self):
        super().setUp()
        self.incoming = Task.objects.create(
            title="in", priority=Priority.HIGH, points=1,
            deadline=self.tomorrow, from_user=self.head, to_user=self.teacher,
        )
        self.outgoing = Task.objects.create(
            title="out", priority=Priority.HIGH, points=1,
            deadline=self.tomorrow, from_user=self.teacher, to_user=self.head,
        )

    def test_my_returns_incoming_only(self):
        self._auth(self.teacher)
        res = self.client.get(f"{self.url}my/")
        self.assertEqual(res.status_code, 200)
        ids = {t["id"] for t in res.data["result"]}
        self.assertIn(str(self.incoming.id), ids)
        self.assertNotIn(str(self.outgoing.id), ids)

    def test_outgoing_returns_outgoing_only(self):
        self._auth(self.teacher)
        res = self.client.get(f"{self.url}outgoing/")
        self.assertEqual(res.status_code, 200)
        ids = {t["id"] for t in res.data["result"]}
        self.assertIn(str(self.outgoing.id), ids)
        self.assertNotIn(str(self.incoming.id), ids)


class TaskStatusPatchTests(_BaseTaskTestCase):
    def setUp(self):
        super().setUp()
        self.task = Task.objects.create(
            title="X", priority=Priority.HIGH, points=1,
            deadline=self.tomorrow, from_user=self.head, to_user=self.teacher,
        )
        self.status_url = f"{self.url}{self.task.id}/status/"

    def test_unauthenticated_returns_401(self):
        res = self.client.patch(self.status_url, {"status": "in_progress"}, format="json")
        self.assertEqual(res.status_code, 401)

    def test_non_assignee_returns_403(self):
        self._auth(self.head)
        res = self.client.patch(self.status_url, {"status": "in_progress"}, format="json")
        self.assertEqual(res.status_code, 403)

    def test_assignee_can_update_status(self):
        self._auth(self.teacher)
        res = self.client.patch(self.status_url, {"status": "completed"}, format="json")
        self.assertEqual(res.status_code, 200)
        self.task.refresh_from_db()
        self.assertEqual(self.task.status, "completed")

    def test_routed_status_rejected(self):
        self._auth(self.teacher)
        res = self.client.patch(self.status_url, {"status": "routed"}, format="json")
        self.assertEqual(res.status_code, 422)

    def test_invalid_status_rejected(self):
        self._auth(self.teacher)
        res = self.client.patch(self.status_url, {"status": "archived"}, format="json")
        self.assertEqual(res.status_code, 422)


class TaskUpdateDeleteTests(_BaseTaskTestCase):
    def setUp(self):
        super().setUp()
        self.task = Task.objects.create(
            title="X", priority=Priority.HIGH, points=1,
            deadline=self.tomorrow, from_user=self.head, to_user=self.teacher,
        )
        self.detail_url = f"{self.url}{self.task.id}/"

    def test_assignee_cannot_update(self):
        self._auth(self.teacher)
        res = self.client.patch(self.detail_url, {"title": "Y"}, format="json")
        self.assertEqual(res.status_code, 403)

    def test_owner_can_update(self):
        self._auth(self.head)
        res = self.client.patch(self.detail_url, {"title": "Y"}, format="json")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data["title"], "Y")

    def test_admin_can_update_foreign_task(self):
        self._auth(self.admin)
        res = self.client.patch(self.detail_url, {"title": "admin-edited"}, format="json")
        self.assertEqual(res.status_code, 200)

    def test_assignee_cannot_delete(self):
        self._auth(self.teacher)
        res = self.client.delete(self.detail_url)
        self.assertEqual(res.status_code, 403)

    def test_owner_delete_is_soft(self):
        self._auth(self.head)
        res = self.client.delete(self.detail_url)
        self.assertEqual(res.status_code, 204)
        self.assertTrue(Task.all_objects.filter(id=self.task.id).exists())
        self.assertFalse(Task.objects.filter(id=self.task.id).exists())

    def test_soft_deleted_returns_404(self):
        self.task.soft_delete()
        self._auth(self.teacher)
        res = self.client.get(self.detail_url)
        self.assertEqual(res.status_code, 404)
