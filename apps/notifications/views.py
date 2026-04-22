from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.notifications.models import Notification
from apps.notifications.serializers import NotificationSerializer
from apps.users.permissions import IsAdmin


class NotificationViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = NotificationSerializer
    lookup_value_regex = "[0-9a-f-]{36}"

    def get_queryset(self):
        qs = Notification.objects.filter(deleted_at__isnull=True)
        if self.action in ("list", "retrieve", "mark_read", "unread_count", "destroy"):
            qs = qs.filter(user=self.request.user)
        return qs

    def get_permissions(self):
        if self.action == "create":
            return [IsAdmin()]
        return [IsAuthenticated()]

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.soft_delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["patch"], url_path="read")
    def mark_read(self, request, pk=None):
        instance = self.get_object()
        instance.is_read = True
        instance.save(update_fields=["is_read", "updated_at"])
        return Response(NotificationSerializer(instance).data)

    @action(detail=False, methods=["get"], url_path="unread-count")
    def unread_count(self, request):
        count = self.get_queryset().filter(is_read=False).count()
        return Response({"count": count})
