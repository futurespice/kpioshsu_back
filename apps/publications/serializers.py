from rest_framework import serializers

from apps.publications.models import Publication


class PublicationSerializer(serializers.ModelSerializer):
    kpi_points = serializers.IntegerField(read_only=True)

    class Meta:
        model = Publication
        fields = [
            "id",
            "user",
            "title",
            "journal",
            "journal_type",
            "pub_date",
            "url",
            "coauthors",
            "kpi_indicator",
            "evidence_file",
            "is_archived",
            "academic_year",
            "kpi_points",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "user", "kpi_points", "created_at", "updated_at"]
