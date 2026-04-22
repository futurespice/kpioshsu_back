from rest_framework import serializers

from apps.approvals.models import Approval


class ApprovalSerializer(serializers.ModelSerializer):
    submitted_at = serializers.DateTimeField(source="created_at", read_only=True)

    class Meta:
        model = Approval
        fields = [
            "id",
            "type",
            "title",
            "from_user",
            "department",
            "document",
            "status",
            "submitted_at",
            "resolved_at",
            "resolved_by",
            "rejection_reason",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "from_user",
            "status",
            "resolved_at",
            "resolved_by",
            "rejection_reason",
            "submitted_at",
            "created_at",
            "updated_at",
        ]


class RejectSerializer(serializers.Serializer):
    reason = serializers.CharField(min_length=1)
