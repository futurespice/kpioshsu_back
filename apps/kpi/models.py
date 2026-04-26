from decimal import Decimal

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from apps.common.models import BaseModel


class PeriodType(models.TextChoices):
    MONTH = "month", "Month"
    SEMESTER = "semester", "Semester"
    YEAR = "year", "Year"


class KPICategory(models.TextChoices):
    SCIENCE = "science", "Наука"
    TEACHING = "teaching", "Учебная работа"
    METHODOLOGY = "methodology", "Методическая работа"
    EDUCATION = "education", "Воспитательная работа"
    LOAD = "load", "Нагрузка"
    OTHER = "other", "Прочее"


class KPI(BaseModel):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")
    weight = models.DecimalField(
        max_digits=5,
        decimal_places=4,
        validators=[
            MinValueValidator(Decimal("0.0000")),
            MaxValueValidator(Decimal("1.0000")),
        ],
    )
    category = models.CharField(
        max_length=20,
        choices=KPICategory.choices,
        default=KPICategory.OTHER,
    )
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_kpis",
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Показатель КПЭ"
        verbose_name_plural = "Показатели КПЭ"
        ordering = ["name"]


class KPIValue(BaseModel):
    user = models.ForeignKey(
        "users.User",
        on_delete=models.CASCADE,
        related_name="kpi_values",
    )
    kpi = models.ForeignKey(
        KPI,
        on_delete=models.CASCADE,
        related_name="values",
    )
    value = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[
            MinValueValidator(Decimal("0")),
            MaxValueValidator(Decimal("100")),
        ],
    )
    period_type = models.CharField(max_length=10, choices=PeriodType.choices)
    period_value = models.CharField(max_length=20)

    def __str__(self):
        return f"{self.user_id} / {self.kpi_id} / {self.period_type}/{self.period_value}"

    class Meta:
        verbose_name = "Значение КПЭ"
        verbose_name_plural = "Значения КПЭ"
        ordering = ["-created_at"]


class KPIResult(BaseModel):
    user = models.ForeignKey(
        "users.User",
        on_delete=models.CASCADE,
        related_name="kpi_results",
    )
    total_value = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[
            MinValueValidator(Decimal("0")),
            MaxValueValidator(Decimal("100")),
        ],
    )
    period_type = models.CharField(max_length=10, choices=PeriodType.choices)
    period_value = models.CharField(max_length=20)

    class Meta:
        verbose_name = "Результат КПЭ"
        verbose_name_plural = "Результаты КПЭ"
        ordering = ["-created_at"]
