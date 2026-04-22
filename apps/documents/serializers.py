from rest_framework import serializers

from apps.documents.models import Document


class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = [
            "id",
            "title",
            "doc_type",
            "user",
            "department",
            "file_path",
            "file_size",
            "mime_type",
            "status",
            "approved_by_dept",
            "approved_by_dean",
            "approved_by_rector",
            "approved_at",
            "rejection_reason",
            "academic_year",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "user",
            "status",
            "approved_by_dept",
            "approved_by_dean",
            "approved_by_rector",
            "approved_at",
            "rejection_reason",
            "created_at",
            "updated_at",
        ]


class ApproveSerializer(serializers.Serializer):
    level = serializers.ChoiceField(choices=["dept", "dean", "rector"])


class RejectSerializer(serializers.Serializer):
    reason = serializers.CharField(min_length=1)
