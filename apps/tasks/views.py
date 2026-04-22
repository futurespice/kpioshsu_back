from django.utils import timezone
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.common.viewsets import BaseViewSet
from apps.tasks.models import Task, TaskStatus
from apps.tasks.permissions import (
    IsTaskAssignee,
    IsTaskCreator,
    IsTaskOwnerOrAdmin,
)
from apps.tasks.serializers import (
    TaskRouteSerializer,
    TaskSerializer,
    TaskStatusSerializer,
)
from apps.users.permissions import IsViceRector


class TaskViewSet(BaseViewSet):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    lookup_value_regex = "[0-9a-f-]{36}"

    def get_queryset(self):
        qs = super().get_queryset()
        params = self.request.query_params
        if params.get("status"):
            qs = qs.filter(status=params["status"])
        if params.get("priority"):
            qs = qs.filter(priority=params["priority"])
        if params.get("from_user"):
            qs = qs.filter(from_user_id=params["from_user"])
        if params.get("to_user"):
            qs = qs.filter(to_user_id=params["to_user"])
        return qs

    def get_permissions(self):
        if self.action == "create":
            return [IsTaskCreator()]
        if self.action == "update_status":
            return [IsAuthenticated(), IsTaskAssignee()]
        if self.action == "route":
            return [IsViceRector()]
        if self.action in ("update", "partial_update", "destroy"):
            return [IsAuthenticated(), IsTaskOwnerOrAdmin()]
        return [IsAuthenticated()]

    def perform_create(self, serializer):
        serializer.save(from_user=self.request.user)

    def _paginate(self, qs):
        page = self.paginate_queryset(qs)
        data = self.get_serializer(page if page is not None else qs, many=True).data
        if page is not None:
            return self.get_paginated_response(data)
        return Response(data)

    @action(detail=False, methods=["get"])
    def my(self, request):
        return self._paginate(self.get_queryset().filter(to_user=request.user))

    @action(detail=False, methods=["get"])
    def outgoing(self, request):
        return self._paginate(self.get_queryset().filter(from_user=request.user))

    @action(
        detail=True,
        methods=["patch"],
        url_path="status",
        url_name="update_status",
    )
    def update_status(self, request, pk=None):
        instance = self.get_object()
        serializer = TaskStatusSerializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(TaskSerializer(instance).data)

    @action(detail=True, methods=["patch"], url_path="route", url_name="route")
    def route(self, request, pk=None):
        instance = self.get_object()
        serializer = TaskRouteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance.routed_to = serializer.validated_data["destination"]
        instance.routed_at = timezone.now()
        instance.status = TaskStatus.ROUTED
        instance.save(
            update_fields=["routed_to", "routed_at", "status", "updated_at"]
        )
        return Response(TaskSerializer(instance).data)
