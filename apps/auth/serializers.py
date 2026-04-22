from rest_framework import serializers

from apps.users.models import User


class LoginSerializer(serializers.Serializer):
    login = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class RefreshSerializer(serializers.Serializer):
    token = serializers.CharField()


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()


class MeSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "full_name",
            "role",
            "department",
            "faculty",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields
