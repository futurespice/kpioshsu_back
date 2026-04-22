from django.db import models

from apps.common.models import BaseModel


class StrategicGoal(BaseModel):
    title = models.CharField(max_length=500)
    current_value = models.DecimalField(max_digits=10, decimal_places=2)
    target_value = models.DecimalField(max_digits=10, decimal_places=2)
    unit = models.CharField(max_length=50, blank=True, default="")
    academic_year = models.CharField(max_length=10)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Стратегическая цель"
        verbose_name_plural = "Стратегические цели"
        ordering = ["-academic_year", "title"]


class GrantStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    COMPLETED = "completed", "Completed"
    PENDING = "pending", "Pending"


class Grant(BaseModel):
    title = models.CharField(max_length=500)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=10, choices=GrantStatus.choices)
    faculty = models.ForeignKey(
        "faculties.Faculty",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="grants",
    )
    year = models.IntegerField()

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Грант"
        verbose_name_plural = "Гранты"
        ordering = ["-year", "title"]


class ProgramStatus(models.TextChoices):
    ACCREDITED = "accredited", "Accredited"
    PENDING = "pending", "Pending"
    REJECTED = "rejected", "Rejected"


class Program(BaseModel):
    title = models.CharField(max_length=500)
    faculty = models.ForeignKey(
        "faculties.Faculty",
        on_delete=models.PROTECT,
        related_name="programs",
    )
    status = models.CharField(max_length=12, choices=ProgramStatus.choices)
    accredited_at = models.DateField(null=True, blank=True)
    expires_at = models.DateField(null=True, blank=True)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Образовательная программа"
        verbose_name_plural = "Образовательные программы"
        ordering = ["title"]
