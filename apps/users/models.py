from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.db import models

from apps.common.models import BaseModel
from apps.common.validators import validate_oshsu_email


class Role(models.IntegerChoices):
    ADMIN = 0, "Admin"
    RECTOR = 1, "Rector"
    VICE_RECTOR = 2, "Vice-Rector"
    SCIENCE_DEP = 3, "Science Department"
    STUDENT_AFFAIRS = 4, "Student Affairs"
    DEAN = 5, "Dean"
    HEAD_OF_DEPT = 6, "Head of Department"
    TEACHER = 7, "Teacher"


class UserManager(BaseUserManager):
    def get_queryset(self):
        return super().get_queryset().filter(deleted_at__isnull=True)

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email обязателен")
        validate_oshsu_email(email)
        email = self.normalize_email(email).lower()
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", Role.ADMIN)
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin, BaseModel):
    email = models.EmailField(unique=True, validators=[validate_oshsu_email])
    full_name = models.CharField(max_length=255, blank=True)
    role = models.PositiveSmallIntegerField(
        choices=Role.choices, default=Role.TEACHER
    )
    department = models.ForeignKey(
        "departments.Department",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="users",
    )
    faculty = models.ForeignKey(
        "faculties.Faculty",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="users",
    )
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self):
        return self.email

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"
        ordering = ["-created_at"]
