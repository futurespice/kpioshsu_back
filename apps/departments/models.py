from django.db import models

from apps.common.models import BaseModel


class Department(BaseModel):
    name = models.CharField(max_length=255)
    short = models.CharField(max_length=10, blank=True, default="")
    faculty = models.ForeignKey(
        "faculties.Faculty",
        on_delete=models.PROTECT,
        related_name="departments",
    )
    head = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="headed_departments",
    )
    target_hours = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Кафедра"
        verbose_name_plural = "Кафедры"
        ordering = ["name"]
