from django.db import models

from apps.common.models import BaseModel


class Faculty(BaseModel):
    name = models.CharField(max_length=255)
    short_name = models.CharField(max_length=20, blank=True, default="")
    dean = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="deaned_faculties",
    )
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Факультет"
        verbose_name_plural = "Факультеты"
        ordering = ["name"]
