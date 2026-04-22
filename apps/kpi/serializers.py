from decimal import Decimal

from django.db.models import Sum
from rest_framework import serializers

from apps.kpi.models import KPI, KPIValue


class KPISerializer(serializers.ModelSerializer):
    class Meta:
        model = KPI
        fields = [
            "id",
            "name",
            "description",
            "weight",
            "is_active",
            "created_by",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_by", "created_at", "updated_at"]

    def validate_weight(self, value):
        instance_id = self.instance.id if self.instance else None
        current_sum = (
            KPI.objects.filter(is_active=True)
            .exclude(id=instance_id)
            .aggregate(total=Sum("weight"))["total"]
            or Decimal("0")
        )
        new_weight = Decimal(str(value))
        if current_sum + new_weight > Decimal("1.0"):
            available = Decimal("1.0") - current_sum
            raise serializers.ValidationError(
                f"Сумма весов превысит 1.0. Доступно: {available}"
            )
        return value


class KPIValueSerializer(serializers.ModelSerializer):
    class Meta:
        model = KPIValue
        fields = [
            "id",
            "user",
            "kpi",
            "value",
            "period_type",
            "period_value",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]
