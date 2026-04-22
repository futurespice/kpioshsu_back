from rest_framework import status, viewsets
from rest_framework.response import Response


class BaseViewSet(viewsets.ModelViewSet):
    """Базовый ViewSet: DELETE выполняет soft_delete вместо hard delete.

    Наследуй от него все ViewSet'ы проекта.
    """

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.soft_delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def get_queryset(self):
        return super().get_queryset().filter(deleted_at__isnull=True)
