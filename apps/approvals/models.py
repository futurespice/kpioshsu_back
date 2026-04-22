from django.db import models

from apps.common.models import BaseModel


class ApprovalType(models.TextChoices):
    UMK = "umk", "УМК"
    REPORT = "report", "Отчёт"
    SYLLABUS = "syllabus", "Силлабус"


class ApprovalStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    APPROVED = "approved", "Approved"
    REJECTED = "rejected", "Rejected"


class Approval(BaseModel):
    type = models.CharField(max_length=10, choices=ApprovalType.choices)
    title = models.CharField(max_length=500)
    from_user = models.ForeignKey(
        "users.User",
        on_delete=models.CASCADE,
        related_name="submitted_approvals",
    )
    department = models.ForeignKey(
        "departments.Department",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approvals",
    )
    document = models.ForeignKey(
        "documents.Document",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approvals",
    )
    status = models.CharField(
        max_length=10,
        choices=ApprovalStatus.choices,
        default=ApprovalStatus.PENDING,
    )
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="resolved_approvals",
    )
    rejection_reason = models.TextField(blank=True, default="")

    def __str__(self):
        return f"{self.type}: {self.title}"

    class Meta:
        verbose_name = "Согласование"
        verbose_name_plural = "Согласования"
        ordering = ["-created_at"]
