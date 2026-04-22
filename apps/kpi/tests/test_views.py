from decimal import Decimal

from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from apps.kpi.models import KPI, KPIResult, KPIValue, PeriodType
from apps.users.models import Role, User


class _AuthMixin:
    def _auth(self, user):
        token = RefreshToken.for_user(user).access_token
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")


class KPIViewSetTests(_AuthMixin, APITestCase):
    url = "/api/kpi/"

    def setUp(self):
        self.admin = User.objects.create_user(
            email="admin@oshsu.kg", password="pass12345", role=Role.ADMIN
        )
        self.head = User.objects.create_user(
            email="head@oshsu.kg", password="pass12345", role=Role.HEAD_OF_DEPT
        )
        self.teacher = User.objects.create_user(
            email="teacher@oshsu.kg", password="pass12345", role=Role.TEACHER
        )

    def test_unauthenticated_returns_401(self):
        res = self.client.get(self.url)
        self.assertEqual(res.status_code, 401)

    def test_authenticated_list_excludes_inactive(self):
        KPI.objects.create(name="A", weight=Decimal("0.3"), is_active=True)
        KPI.objects.create(name="B", weight=Decimal("0.4"), is_active=False)
        self._auth(self.teacher)
        res = self.client.get(self.url)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data["count"], 1)

    def test_teacher_cannot_create(self):
        self._auth(self.teacher)
        res = self.client.post(
            self.url, {"name": "X", "weight": "0.1"}, format="json"
        )
        self.assertEqual(res.status_code, 403)

    def test_head_of_dept_can_create(self):
        self._auth(self.head)
        res = self.client.post(
            self.url, {"name": "Наука", "weight": "0.4"}, format="json"
        )
        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.data["name"], "Наука")
        self.assertEqual(res.data["created_by"], self.head.id)

    def test_weight_sum_exceeding_one_rejected(self):
        KPI.objects.create(name="A", weight=Decimal("0.7"))
        self._auth(self.admin)
        res = self.client.post(
            self.url, {"name": "B", "weight": "0.4"}, format="json"
        )
        self.assertEqual(res.status_code, 422)

    def test_weight_sum_equal_to_one_allowed(self):
        KPI.objects.create(name="A", weight=Decimal("0.7"))
        self._auth(self.admin)
        res = self.client.post(
            self.url, {"name": "B", "weight": "0.3"}, format="json"
        )
        self.assertEqual(res.status_code, 201)

    def test_update_excludes_self_from_weight_sum(self):
        kpi = KPI.objects.create(name="A", weight=Decimal("0.5"))
        self._auth(self.admin)
        res = self.client.patch(
            f"{self.url}{kpi.id}/", {"weight": "0.9"}, format="json"
        )
        self.assertEqual(res.status_code, 200)

    def test_delete_deactivates_not_soft_deletes(self):
        kpi = KPI.objects.create(name="A", weight=Decimal("0.3"))
        self._auth(self.admin)
        res = self.client.delete(f"{self.url}{kpi.id}/")
        self.assertEqual(res.status_code, 204)
        kpi.refresh_from_db()
        self.assertFalse(kpi.is_active)
        self.assertIsNone(kpi.deleted_at)

    def test_head_of_dept_cannot_delete(self):
        kpi = KPI.objects.create(name="A", weight=Decimal("0.3"))
        self._auth(self.head)
        res = self.client.delete(f"{self.url}{kpi.id}/")
        self.assertEqual(res.status_code, 403)


class KPIValueCreateViewTests(_AuthMixin, APITestCase):
    url = "/api/kpi/value/"

    def setUp(self):
        self.admin = User.objects.create_user(
            email="admin@oshsu.kg", password="pass12345", role=Role.ADMIN
        )
        self.teacher = User.objects.create_user(
            email="teacher@oshsu.kg", password="pass12345", role=Role.TEACHER
        )
        self.kpi = KPI.objects.create(name="A", weight=Decimal("0.5"))
        self.payload = {
            "user": str(self.teacher.id),
            "kpi": str(self.kpi.id),
            "value": "80",
            "period_type": "month",
            "period_value": "2026-04",
        }

    def test_unauthenticated_returns_401(self):
        res = self.client.post(self.url, self.payload, format="json")
        self.assertEqual(res.status_code, 401)

    def test_teacher_cannot_create(self):
        self._auth(self.teacher)
        res = self.client.post(self.url, self.payload, format="json")
        self.assertEqual(res.status_code, 403)

    def test_admin_can_create(self):
        self._auth(self.admin)
        res = self.client.post(self.url, self.payload, format="json")
        self.assertEqual(res.status_code, 201)
        self.assertEqual(Decimal(res.data["value"]), Decimal("80.00"))

    def test_value_out_of_range_rejected(self):
        self._auth(self.admin)
        bad = {**self.payload, "value": "150"}
        res = self.client.post(self.url, bad, format="json")
        self.assertEqual(res.status_code, 422)

    def test_invalid_period_type_rejected(self):
        self._auth(self.admin)
        bad = {**self.payload, "period_type": "decade"}
        res = self.client.post(self.url, bad, format="json")
        self.assertEqual(res.status_code, 422)

    def test_posting_value_creates_kpi_result(self):
        self._auth(self.admin)
        self.client.post(self.url, self.payload, format="json")
        self.assertEqual(KPIResult.objects.count(), 1)
        result = KPIResult.objects.first()
        # Формула ТЗ v2 §4.1: 80 × 0.5 = 40.00
        self.assertEqual(result.total_value, Decimal("40.00"))

    def test_second_post_upserts_same_result(self):
        self._auth(self.admin)
        self.client.post(self.url, self.payload, format="json")
        # Второе значение того же периода → update, не duplicate
        other_kpi = KPI.objects.create(name="B", weight=Decimal("0.3"))
        self.client.post(
            self.url,
            {**self.payload, "kpi": str(other_kpi.id), "value": "50"},
            format="json",
        )
        self.assertEqual(KPIResult.objects.count(), 1)
        result = KPIResult.objects.first()
        # 80*0.5 + 50*0.3 = 40 + 15 = 55.00
        self.assertEqual(result.total_value, Decimal("55.00"))


class KPIValueListViewTests(_AuthMixin, APITestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            email="admin@oshsu.kg", password="pass12345", role=Role.ADMIN
        )
        self.teacher = User.objects.create_user(
            email="t@oshsu.kg", password="pass12345", role=Role.TEACHER
        )
        self.kpi = KPI.objects.create(name="A", weight=Decimal("0.5"))
        KPIValue.objects.create(
            user=self.teacher,
            kpi=self.kpi,
            value=Decimal("80"),
            period_type=PeriodType.MONTH,
            period_value="2026-04",
        )

    def test_unauthenticated_returns_401(self):
        res = self.client.get(f"/api/kpi/value/{self.teacher.id}/")
        self.assertEqual(res.status_code, 401)

    def test_returns_user_values(self):
        self._auth(self.admin)
        res = self.client.get(f"/api/kpi/value/{self.teacher.id}/")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data["count"], 1)


class TeacherKPIResultViewTests(_AuthMixin, APITestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            email="admin@oshsu.kg", password="pass12345", role=Role.ADMIN
        )
        self.teacher = User.objects.create_user(
            email="t@oshsu.kg", password="pass12345", role=Role.TEACHER
        )

    def test_unauthenticated_returns_401(self):
        res = self.client.get(f"/api/kpi/result/teacher/{self.teacher.id}/")
        self.assertEqual(res.status_code, 401)

    def test_empty_returns_zero(self):
        self._auth(self.admin)
        res = self.client.get(
            f"/api/kpi/result/teacher/{self.teacher.id}/",
            {"period_type": "month", "period_value": "2026-04"},
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data["total_value"], "0.00")

    def test_returns_computed_value(self):
        kpi = KPI.objects.create(name="A", weight=Decimal("0.5"))
        # Пишем через endpoint, чтобы сработал upsert KPIResult
        self._auth(self.admin)
        self.client.post(
            "/api/kpi/value/",
            {
                "user": str(self.teacher.id),
                "kpi": str(kpi.id),
                "value": "80",
                "period_type": "month",
                "period_value": "2026-04",
            },
            format="json",
        )
        res = self.client.get(
            f"/api/kpi/result/teacher/{self.teacher.id}/",
            {"period_type": "month", "period_value": "2026-04"},
        )
        self.assertEqual(res.status_code, 200)
        # Формула ТЗ v2: 80 × 0.5 = 40.00
        self.assertEqual(res.data["total_value"], "40.00")
        self.assertEqual(res.data["period_type"], "month")
