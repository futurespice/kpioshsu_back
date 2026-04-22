from django.db import models

from apps.common.models import BaseModel


class DocType(models.TextChoices):
    UMK = "umk", "УМК"
    REPORT = "report", "Отчёт"
    SYLLABUS = "syllabus", "Силлабус"
    WORK_PROGRAM = "work_program", "Рабочая программа"
    METHOD_GUIDE = "method_guide", "Методические указания"


class DocumentStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    APPROVED = "approved", "Approved"
    REJECTED = "rejected", "Rejected"


class Document(BaseModel):
    title = models.CharField(max_length=500)
    doc_type = models.CharField(max_length=20, choices=DocType.choices)
    user = models.ForeignKey(
        "users.User", on_delete=models.CASCADE, related_name="documents"
    )
    department = models.ForeignKey(
        "departments.Department",
        on_delete=models.PROTECT,
        related_name="documents",
    )
    file_path = models.CharField(max_length=1000)
    file_size = models.IntegerField(null=True, blank=True)
    mime_type = models.CharField(max_length=100, blank=True, default="")
    status = models.CharField(
        max_length=10,
        choices=DocumentStatus.choices,
        default=DocumentStatus.PENDING,
    )
    approved_by_dept = models.BooleanField(default=False)
    approved_by_dean = models.BooleanField(default=False)
    approved_by_rector = models.BooleanField(default=False)
    approved_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True, default="")
    academic_year = models.CharField(max_length=10)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Документ"
        verbose_name_plural = "Документы"
        ordering = ["-created_at"]
