from decimal import Decimal

from django.test import TestCase

from apps.kpi.models import KPI, KPIValue, PeriodType
from apps.kpi.services import calculate_teacher_kpi
from apps.users.models import User


class CalculateTeacherKPITests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="t@oshsu.kg", password="pass12345"
        )
        self.period_type = PeriodType.MONTH
        self.period_value = "2026-04"

    def test_no_values_returns_zero(self):
        result = calculate_teacher_kpi(
            self.user.id, self.period_type, self.period_value
        )
        self.assertEqual(result, Decimal("0.00"))

    def test_single_value_formula(self):
        kpi = KPI.objects.create(name="A", weight=Decimal("0.5"))
        KPIValue.objects.create(
            user=self.user,
            kpi=kpi,
            value=Decimal("80"),
            period_type=self.period_type,
            period_value=self.period_value,
        )
        # 80 × 0.5 = 40.00
        result = calculate_teacher_kpi(
            self.user.id, self.period_type, self.period_value
        )
        self.assertEqual(result, Decimal("40.00"))

    def test_multiple_values_summed(self):
        k1 = KPI.objects.create(name="A", weight=Decimal("0.3"))
        k2 = KPI.objects.create(name="B", weight=Decimal("0.5"))
        k3 = KPI.objects.create(name="C", weight=Decimal("0.2"))
        for kpi, val in [(k1, 80), (k2, 90), (k3, 70)]:
            KPIValue.objects.create(
                user=self.user,
                kpi=kpi,
                value=Decimal(val),
                period_type=self.period_type,
                period_value=self.period_value,
            )
        # 80*0.3 + 90*0.5 + 70*0.2 = 24 + 45 + 14 = 83.00
        result = calculate_teacher_kpi(
            self.user.id, self.period_type, self.period_value
        )
        self.assertEqual(result, Decimal("83.00"))

    def test_inactive_kpi_excluded(self):
        active = KPI.objects.create(name="A", weight=Decimal("0.5"), is_active=True)
        inactive = KPI.objects.create(
            name="B", weight=Decimal("0.3"), is_active=False
        )
        KPIValue.objects.create(
            user=self.user,
            kpi=active,
            value=Decimal("80"),
            period_type=self.period_type,
            period_value=self.period_value,
        )
        KPIValue.objects.create(
            user=self.user,
            kpi=inactive,
            value=Decimal("100"),
            period_type=self.period_type,
            period_value=self.period_value,
        )
        # Only active counted: 80 × 0.5 = 40.00
        result = calculate_teacher_kpi(
            self.user.id, self.period_type, self.period_value
        )
        self.assertEqual(result, Decimal("40.00"))

    def test_different_period_not_counted(self):
        kpi = KPI.objects.create(name="A", weight=Decimal("0.5"))
        KPIValue.objects.create(
            user=self.user,
            kpi=kpi,
            value=Decimal("80"),
            period_type=PeriodType.MONTH,
            period_value="2025-01",
        )
        result = calculate_teacher_kpi(
            self.user.id, PeriodType.MONTH, "2026-04"
        )
        self.assertEqual(result, Decimal("0.00"))

    def test_result_quantized_to_two_decimals(self):
        kpi = KPI.objects.create(name="A", weight=Decimal("0.3333"))
        KPIValue.objects.create(
            user=self.user,
            kpi=kpi,
            value=Decimal("33.33"),
            period_type=self.period_type,
            period_value=self.period_value,
        )
        # 33.33 × 0.3333 = 11.108889 → 11.11
        result = calculate_teacher_kpi(
            self.user.id, self.period_type, self.period_value
        )
        self.assertEqual(result.as_tuple().exponent, -2)
