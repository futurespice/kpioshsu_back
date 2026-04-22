from django.db import models

from apps.common.models import BaseModel


class PlanerkaPriority(models.TextChoices):
    HIGH = "high", "High"
    MEDIUM = "medium", "Medium"
    LOW = "low", "Low"


class Planerka(BaseModel):
    title = models.CharField(max_length=500)
    description = models.TextField(blank=True, default="")
    faculty = models.CharField(max_length=255, blank=True, default="")
    priority = models.CharField(max_length=10, choices=PlanerkaPriority.choices)
    deadline = models.DateField()
    points = models.IntegerField(null=True, blank=True)
    hours = models.IntegerField(null=True, blank=True)
    status = models.CharField(max_length=50)
    created_by = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="planerka_events",
    )

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Событие планёрки"
        verbose_name_plural = "События планёрки"
        ordering = ["-deadline", "-created_at"]
