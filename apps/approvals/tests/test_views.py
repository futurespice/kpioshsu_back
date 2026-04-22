from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from apps.approvals.models import Approval, ApprovalStatus, ApprovalType
from apps.users.models import Role, User


class _AuthMixin:
    def _auth(self, user):
        token = RefreshToken.for_user(user).access_token
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")


class _BaseApprovalTestCase(_AuthMixin, APITestCase):
    url = "/api/approvals/"

    def setUp(self):
        self.dean = User.objects.create_user(
            email="dean@oshsu.kg", password="p", role=Role.DEAN
        )
        self.head = User.objects.create_user(
            email="head@oshsu.kg", password="p", role=Role.HEAD_OF_DEPT
        )
        self.teacher = User.objects.create_user(
            email="t@oshsu.kg", password="p", role=Role.TEACHER
        )
        self.vice = User.objects.create_user(
            email="vice@oshsu.kg", password="p", role=Role.VICE_RECTOR
        )
        self.rector = User.objects.create_user(
            email="rector@oshsu.kg", password="p", role=Role.RECTOR
        )


class ApprovalCreateTests(_BaseApprovalTestCase):
    payload = {"type": "umk", "title": "УМК по БД"}

    def test_unauthenticated_returns_401(self):
        res = self.client.post(self.url, self.payload, format="json")
        self.assertEqual(res.status_code, 401)

    def test_vice_rector_cannot_submit(self):
        self._auth(self.vice)
        res = self.client.post(self.url, self.payload, format="json")
        self.assertEqual(res.status_code, 403)

    def test_dean_can_submit(self):
        self._auth(self.dean)
        res = self.client.post(self.url, self.payload, format="json")
        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.data["from_user"], self.dean.id)
        self.assertEqual(res.data["status"], ApprovalStatus.PENDING)
        self.assertIn("submitted_at", res.data)

    def test_teacher_can_submit(self):
        self._auth(self.teacher)
        res = self.client.post(self.url, self.payload, format="json")
        self.assertEqual(res.status_code, 201)

    def test_invalid_type_returns_422(self):
        self._auth(self.dean)
        bad = {"type": "dissertation", "title": "X"}
        res = self.client.post(self.url, bad, format="json")
        self.assertEqual(res.status_code, 422)


class ApprovalListTests(_BaseApprovalTestCase):
    def setUp(self):
        super().setUp()
        self.pending = Approval.objects.create(
            type=ApprovalType.UMK, title="Pending",
            from_user=self.dean, status=ApprovalStatus.PENDING,
        )
        self.approved = Approval.objects.create(
            type=ApprovalType.REPORT, title="Approved",
            from_user=self.dean, status=ApprovalStatus.APPROVED,
        )

    def test_teacher_cannot_list(self):
        self._auth(self.teacher)
        res = self.client.get(self.url)
        self.assertEqual(res.status_code, 403)

    def test_vice_rector_can_list(self):
        self._auth(self.vice)
        res = self.client.get(self.url)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data["count"], 2)

    def test_filter_by_status(self):
        self._auth(self.vice)
        res = self.client.get(self.url, {"status": "pending"})
        self.assertEqual(res.data["count"], 1)
        self.assertEqual(res.data["result"][0]["id"], str(self.pending.id))


class ApprovalApproveTests(_BaseApprovalTestCase):
    def setUp(self):
        super().setUp()
        self.approval = Approval.objects.create(
            type=ApprovalType.UMK, title="X", from_user=self.dean
        )
        self.approve_url = f"{self.url}{self.approval.id}/approve/"

    def test_dean_cannot_approve(self):
        self._auth(self.dean)
        res = self.client.patch(self.approve_url)
        self.assertEqual(res.status_code, 403)

    def test_vice_rector_can_approve(self):
        self._auth(self.vice)
        res = self.client.patch(self.approve_url)
        self.assertEqual(res.status_code, 200)
        self.approval.refresh_from_db()
        self.assertEqual(self.approval.status, ApprovalStatus.APPROVED)
        self.assertIsNotNone(self.approval.resolved_at)
        self.assertEqual(self.approval.resolved_by, self.vice)


class ApprovalRejectTests(_BaseApprovalTestCase):
    def setUp(self):
        super().setUp()
        self.approval = Approval.objects.create(
            type=ApprovalType.UMK, title="X", from_user=self.dean
        )
        self.reject_url = f"{self.url}{self.approval.id}/reject/"

    def test_teacher_cannot_reject(self):
        self._auth(self.teacher)
        res = self.client.patch(self.reject_url, {"reason": "x"}, format="json")
        self.assertEqual(res.status_code, 403)

    def test_vice_rector_can_reject_with_reason(self):
        self._auth(self.vice)
        res = self.client.patch(
            self.reject_url, {"reason": "Недостаточно полно"}, format="json"
        )
        self.assertEqual(res.status_code, 200)
        self.approval.refresh_from_db()
        self.assertEqual(self.approval.status, ApprovalStatus.REJECTED)
        self.assertEqual(self.approval.rejection_reason, "Недостаточно полно")
        self.assertEqual(self.approval.resolved_by, self.vice)

    def test_reject_without_reason_returns_422(self):
        self._auth(self.vice)
        res = self.client.patch(self.reject_url, {}, format="json")
        self.assertEqual(res.status_code, 422)
