from decimal import Decimal

from rest_framework import serializers

from apps.department_load.models import DeptLoad


class DeptLoadSerializer(serializers.ModelSerializer):
    pct = serializers.SerializerMethodField()

    class Meta:
        model = DeptLoad
        fields = [
            "id",
            "department",
            "academic_year",
            "semester",
            "target_hours",
            "actual_hours",
            "pct",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "pct", "created_at", "updated_at"]

    def get_pct(self, obj):
        if not obj.target_hours:
            return "0.00"
        val = Decimal(obj.actual_hours) / Decimal(obj.target_hours) * 100
        return str(val.quantize(Decimal("0.01")))
