from rest_framework import serializers

from apps.strategic.models import Grant, Program, StrategicGoal


class StrategicGoalSerializer(serializers.ModelSerializer):
    class Meta:
        model = StrategicGoal
        fields = [
            "id",
            "title",
            "current_value",
            "target_value",
            "unit",
            "academic_year",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class GrantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Grant
        fields = [
            "id",
            "title",
            "amount",
            "status",
            "faculty",
            "year",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class ProgramSerializer(serializers.ModelSerializer):
    class Meta:
        model = Program
        fields = [
            "id",
            "title",
            "faculty",
            "status",
            "accredited_at",
            "expires_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
