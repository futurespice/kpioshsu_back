from rest_framework import serializers

from apps.departments.models import Department
from apps.users.models import Role


class DepartmentSerializer(serializers.ModelSerializer):
    teacher_count = serializers.SerializerMethodField()

    class Meta:
        model = Department
        fields = [
            "id",
            "name",
            "short",
            "faculty",
            "head",
            "target_hours",
            "teacher_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "teacher_count", "created_at", "updated_at"]

    def get_teacher_count(self, obj):
        return obj.users.filter(role=Role.TEACHER, is_active=True).count()
