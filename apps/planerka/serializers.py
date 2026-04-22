from rest_framework import serializers

from apps.planerka.models import Planerka


class PlanerkaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Planerka
        fields = [
            "id",
            "title",
            "description",
            "faculty",
            "priority",
            "deadline",
            "points",
            "hours",
            "status",
            "created_by",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_by", "created_at", "updated_at"]
