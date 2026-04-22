from django.db.models import Count, Q
from django.utils import timezone
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.common.permissions import make_role_permission
from apps.common.viewsets import BaseViewSet
from apps.departments.models import Department
from apps.documents.models import Document, DocType, DocumentStatus
from apps.documents.permissions import IsDocumentOwnerOrAdmin
from apps.documents.serializers import (
    ApproveSerializer,
    DocumentSerializer,
    RejectSerializer,
)
from apps.users.models import Role


_IsUploader = make_role_permission(Role.TEACHER, Role.HEAD_OF_DEPT, Role.ADMIN)
_IsApprover = make_role_permission(
    Role.DEAN, Role.VICE_RECTOR, Role.RECTOR, Role.ADMIN
)
_IsUmkReader = make_role_permission(Role.VICE_RECTOR, Role.RECTOR, Role.ADMIN)


class DocumentViewSet(BaseViewSet):
    queryset = Document.objects.all()
    serializer_class = DocumentSerializer
    lookup_value_regex = "[0-9a-f-]{36}"

    def get_queryset(self):
        qs = super().get_queryset()
        p = self.request.query_params
        if p.get("dept_id"):
            qs = qs.filter(department_id=p["dept_id"])
        if p.get("type"):
            qs = qs.filter(doc_type=p["type"])
        if p.get("status"):
            qs = qs.filter(status=p["status"])
        if p.get("year"):
            qs = qs.filter(academic_year=p["year"])
        return qs

    def get_permissions(self):
        if self.action == "create":
            return [_IsUploader()]
        if self.action in ("approve", "reject"):
            return [_IsApprover()]
        if self.action == "umk_status":
            return [_IsUmkReader()]
        if self.action == "destroy":
            return [IsAuthenticated(), IsDocumentOwnerOrAdmin()]
        return [IsAuthenticated()]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=["patch"])
    def approve(self, request, pk=None):
        instance = self.get_object()
        serializer = ApproveSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        level = serializer.validated_data["level"]

        if level == "dept":
            instance.approved_by_dept = True
        elif level == "dean":
            instance.approved_by_dean = True
        elif level == "rector":
            instance.approved_by_rector = True

        if (
            instance.approved_by_dept
            and instance.approved_by_dean
            and instance.approved_by_rector
        ):
            instance.status = DocumentStatus.APPROVED
            instance.approved_at = timezone.now()

        instance.save()
        return Response(DocumentSerializer(instance).data)

    @action(detail=True, methods=["patch"])
    def reject(self, request, pk=None):
        instance = self.get_object()
        serializer = RejectSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance.status = DocumentStatus.REJECTED
        instance.rejection_reason = serializer.validated_data["reason"]
        instance.save()
        return Response(DocumentSerializer(instance).data)

    @action(detail=True, methods=["get"])
    def download(self, request, pk=None):
        instance = self.get_object()
        return Response(
            {
                "file_path": instance.file_path,
                "mime_type": instance.mime_type,
                "file_size": instance.file_size,
            }
        )

    @action(
        detail=False,
        methods=["get"],
        url_path="umk/status",
        url_name="umk_status",
    )
    def umk_status(self, request):
        qs = Department.objects.annotate(
            umk_total=Count(
                "documents",
                filter=Q(
                    documents__doc_type=DocType.UMK,
                    documents__deleted_at__isnull=True,
                ),
            ),
            umk_approved=Count(
                "documents",
                filter=Q(
                    documents__doc_type=DocType.UMK,
                    documents__status=DocumentStatus.APPROVED,
                    documents__deleted_at__isnull=True,
                ),
            ),
            umk_pending=Count(
                "documents",
                filter=Q(
                    documents__doc_type=DocType.UMK,
                    documents__status=DocumentStatus.PENDING,
                    documents__deleted_at__isnull=True,
                ),
            ),
            umk_rejected=Count(
                "documents",
                filter=Q(
                    documents__doc_type=DocType.UMK,
                    documents__status=DocumentStatus.REJECTED,
                    documents__deleted_at__isnull=True,
                ),
            ),
        )
        data = [
            {
                "department": str(d.id),
                "name": d.name,
                "total": d.umk_total,
                "approved": d.umk_approved,
                "pending": d.umk_pending,
                "rejected": d.umk_rejected,
            }
            for d in qs
        ]
        return Response(data)
