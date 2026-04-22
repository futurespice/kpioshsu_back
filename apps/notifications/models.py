from django.db import models

from apps.common.models import BaseModel


class NotificationType(models.TextChoices):
    ALERT = "alert", "Alert"
    DEADLINE = "deadline", "Deadline"
    ACHIEVEMENT = "achievement", "Achievement"
    INFO = "info", "Info"


class Notification(BaseModel):
    user = models.ForeignKey(
        "users.User",
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    type = models.CharField(
        max_length=20,
        choices=NotificationType.choices,
        default=NotificationType.INFO,
    )
    title = models.CharField(max_length=255)
    message = models.TextField(blank=True, default="")
    link = models.CharField(max_length=500, blank=True, default="")
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Уведомление"
        verbose_name_plural = "Уведомления"
        ordering = ["-created_at"]
