from django.db import models

from apps.common.models import BaseModel


class Priority(models.TextChoices):
    HIGH = "high", "High"
    MEDIUM = "medium", "Medium"
    LOW = "low", "Low"


class TaskStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    IN_PROGRESS = "in_progress", "In progress"
    COMPLETED = "completed", "Completed"
    ROUTED = "routed", "Routed"


class Task(BaseModel):
    title = models.CharField(max_length=500)
    description = models.TextField(blank=True, default="")
    priority = models.CharField(max_length=10, choices=Priority.choices)
    status = models.CharField(
        max_length=20, choices=TaskStatus.choices, default=TaskStatus.PENDING
    )
    points = models.IntegerField(default=0)
    deadline = models.DateField()

    from_user = models.ForeignKey(
        "users.User",
        on_delete=models.PROTECT,
        related_name="outgoing_tasks",
    )
    to_user = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="incoming_tasks",
    )
    to_dept = models.ForeignKey(
        "departments.Department",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="tasks",
    )
    faculty = models.ForeignKey(
        "faculties.Faculty",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="tasks",
    )

    routed_to = models.CharField(max_length=255, blank=True, default="")
    routed_at = models.DateTimeField(null=True, blank=True)
    hours = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Задача"
        verbose_name_plural = "Задачи"
        ordering = ["-created_at"]
