from django.utils import timezone
from rest_framework import serializers

from apps.tasks.models import Task, TaskStatus


class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = [
            "id",
            "title",
            "description",
            "priority",
            "status",
            "points",
            "deadline",
            "from_user",
            "to_user",
            "to_dept",
            "faculty",
            "routed_to",
            "routed_at",
            "hours",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "from_user",
            "routed_to",
            "routed_at",
            "created_at",
            "updated_at",
        ]

    def validate_deadline(self, value):
        if self.instance is None and value < timezone.now().date():
            raise serializers.ValidationError("Дедлайн не может быть в прошлом")
        return value


class TaskRouteSerializer(serializers.Serializer):
    destination = serializers.CharField(max_length=255)


class TaskStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = ["status"]

    def validate_status(self, value):
        allowed = {
            TaskStatus.PENDING,
            TaskStatus.IN_PROGRESS,
            TaskStatus.COMPLETED,
        }
        if value not in allowed:
            raise serializers.ValidationError(
                "Статус должен быть pending, in_progress или completed"
            )
        return value
