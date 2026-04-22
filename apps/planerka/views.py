from rest_framework import mixins, status, viewsets
from rest_framework.response import Response

from apps.planerka.models import Planerka
from apps.planerka.serializers import PlanerkaSerializer
from apps.users.permissions import IsManagement, IsViceRector


class PlanerkaViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = PlanerkaSerializer
    lookup_value_regex = "[0-9a-f-]{36}"

    def get_queryset(self):
        return Planerka.objects.filter(deleted_at__isnull=True)

    def get_permissions(self):
        if self.action == "list":
            return [IsManagement()]
        return [IsViceRector()]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.soft_delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
