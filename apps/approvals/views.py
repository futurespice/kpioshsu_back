from django.utils import timezone
from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.approvals.models import Approval, ApprovalStatus
from apps.approvals.serializers import ApprovalSerializer, RejectSerializer
from apps.common.permissions import make_role_permission
from apps.users.models import Role


_IsSubmitter = make_role_permission(
    Role.DEAN, Role.HEAD_OF_DEPT, Role.TEACHER, Role.ADMIN
)
_IsReviewer = make_role_permission(Role.VICE_RECTOR, Role.RECTOR, Role.ADMIN)


class ApprovalViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = ApprovalSerializer
    lookup_value_regex = "[0-9a-f-]{36}"

    def get_queryset(self):
        qs = Approval.objects.filter(deleted_at__isnull=True)
        status_q = self.request.query_params.get("status")
        if status_q:
            qs = qs.filter(status=status_q)
        return qs

    def get_permissions(self):
        if self.action == "create":
            return [_IsSubmitter()]
        return [_IsReviewer()]

    def perform_create(self, serializer):
        serializer.save(from_user=self.request.user)

    @action(detail=True, methods=["patch"])
    def approve(self, request, pk=None):
        instance = self.get_object()
        instance.status = ApprovalStatus.APPROVED
        instance.resolved_at = timezone.now()
        instance.resolved_by = request.user
        instance.save()
        return Response(ApprovalSerializer(instance).data)

    @action(detail=True, methods=["patch"])
    def reject(self, request, pk=None):
        instance = self.get_object()
        serializer = RejectSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance.status = ApprovalStatus.REJECTED
        instance.rejection_reason = serializer.validated_data["reason"]
        instance.resolved_at = timezone.now()
        instance.resolved_by = request.user
        instance.save()
        return Response(ApprovalSerializer(instance).data)
