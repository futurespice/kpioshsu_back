from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.common.viewsets import BaseViewSet
from apps.publications.models import JOURNAL_POINTS, Publication
from apps.publications.permissions import IsPublicationOwnerOrAdmin
from apps.publications.serializers import PublicationSerializer
from apps.users.permissions import IsTeacher


def _parse_bool(value):
    if value is None:
        return None
    lowered = str(value).lower()
    if lowered in ("true", "1", "yes"):
        return True
    if lowered in ("false", "0", "no"):
        return False
    return None


class PublicationViewSet(BaseViewSet):
    queryset = Publication.objects.all()
    serializer_class = PublicationSerializer
    lookup_value_regex = "[0-9a-f-]{36}"

    def get_queryset(self):
        qs = super().get_queryset()
        p = self.request.query_params
        if p.get("user_id"):
            qs = qs.filter(user_id=p["user_id"])
        if p.get("year"):
            qs = qs.filter(academic_year=p["year"])
        if p.get("type"):
            qs = qs.filter(journal_type=p["type"])
        archived = _parse_bool(p.get("archived"))
        if archived is not None:
            qs = qs.filter(is_archived=archived)
        return qs

    def get_permissions(self):
        if self.action == "create":
            return [IsTeacher()]
        if self.action in ("update", "partial_update", "destroy"):
            return [IsAuthenticated(), IsPublicationOwnerOrAdmin()]
        return [IsAuthenticated()]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=["get"])
    def my(self, request):
        qs = self.get_queryset().filter(user=request.user)
        grouped = {}
        for pub in qs:
            grouped.setdefault(pub.academic_year, []).append(
                PublicationSerializer(pub).data
            )
        return Response(grouped)


class PublicationStatsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, user_id):
        qs = Publication.objects.filter(
            user_id=user_id, deleted_at__isnull=True
        )
        by_type = {}
        total_points = 0
        for pub in qs:
            by_type[pub.journal_type] = by_type.get(pub.journal_type, 0) + 1
            total_points += JOURNAL_POINTS.get(pub.journal_type, 0)
        return Response(
            {
                "user": str(user_id),
                "total_count": qs.count(),
                "by_type": by_type,
                "total_points": total_points,
            }
        )
