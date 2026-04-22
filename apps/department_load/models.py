from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from apps.common.models import BaseModel


class DeptLoad(BaseModel):
    department = models.ForeignKey(
        "departments.Department",
        on_delete=models.PROTECT,
        related_name="loads",
    )
    academic_year = models.CharField(max_length=10)
    semester = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(2)]
    )
    target_hours = models.IntegerField()
    actual_hours = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.department_id} {self.academic_year}/{self.semester}"

    class Meta:
        verbose_name = "Нагрузка кафедры"
        verbose_name_plural = "Нагрузки кафедр"
        unique_together = [("department", "academic_year", "semester")]
        ordering = ["-academic_year", "-semester"]
