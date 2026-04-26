# Skill: DRF Patterns — kpioshsu_back
Паттерны Django REST Framework, специфичные для этого проекта.
Читай перед написанием любого ViewSet, Serializer или Permission.

---

## Кастомный Pagination (ОБЯЗАТЕЛЬНО)

Фронтенд ждёт `"result"` (не `"results"`). Стандартный DRF возвращает `"results"`.

```python
# config/pagination.py
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class StandardPagination(PageNumberPagination):
    page_size             = 20
    page_size_query_param = "page_size"
    max_page_size         = 100

    def get_paginated_response(self, data):
        return Response({
            "count":     self.page.paginator.count,
            "page":      self.page.number,
            "page_size": self.page.paginator.per_page,
            "next":      self.get_next_link(),
            "previous":  self.get_previous_link(),
            "result":    data,  # НЕ "results"
        })


# settings.py
REST_FRAMEWORK = {
    "DEFAULT_PAGINATION_CLASS": "config.pagination.StandardPagination",
    ...
}
```

---

## Role-based Permissions

```python
# apps/common/permissions.py
from rest_framework.permissions import BasePermission
from apps.users.models import Role


def make_role_permission(*roles):
    """Фабрика permission-классов по ролям."""
    class RolePermission(BasePermission):
        def has_permission(self, request, view):
            return (
                request.user.is_authenticated
                and request.user.role in roles
            )
    return RolePermission


# Готовые классы
IsAdmin       = make_role_permission(Role.ADMIN)
IsRector      = make_role_permission(Role.RECTOR, Role.ADMIN)
IsViceRector  = make_role_permission(Role.VICE_RECTOR, Role.ADMIN)
IsDean        = make_role_permission(Role.DEAN, Role.ADMIN)
IsHeadOfDept  = make_role_permission(Role.HEAD_OF_DEPT, Role.ADMIN)
IsTeacher     = make_role_permission(Role.TEACHER)
IsManagement  = make_role_permission(Role.RECTOR, Role.VICE_RECTOR, Role.ADMIN)
```

### Использование в ViewSet с разными правами per-action

```python
class TaskViewSet(viewsets.ModelViewSet):
    def get_permissions(self):
        if self.action in ["create"]:
            return [IsHeadOfDept()]
        if self.action in ["list", "retrieve"]:
            return [IsAuthenticated()]
        if self.action in ["destroy"]:
            return [IsAdmin()]
        return [IsAuthenticated()]
```

---

## Стандартный Error Response

```python
# apps/common/exceptions.py
from rest_framework.views import exception_handler
from rest_framework.response import Response


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is not None:
        response.data = {
            "error":   str(exc),
            "code":    exc.__class__.__name__.upper(),
            "details": response.data,
        }
    return response


# settings.py
REST_FRAMEWORK = {
    "EXCEPTION_HANDLER": "apps.common.exceptions.custom_exception_handler",
    ...
}
```

---

## JWT Auth (SimpleJWT)

```python
# КРИТИЧНО: ключ "acces" — без второй 's'
# apps/auth/views.py
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.response import Response
from rest_framework.views import APIView


class LoginView(APIView):
    permission_classes = []

    def post(self, request):
        # ... валидация login/password ...
        refresh = RefreshToken.for_user(user)
        return Response({
            "acces":   str(refresh.access_token),  # опечатка намеренная!
            "refresh": str(refresh),
        })


class RefreshView(APIView):
    permission_classes = []

    def post(self, request):
        token = request.data.get("token")
        refresh = RefreshToken(token)
        return Response({
            "acces":   str(refresh.access_token),  # опечатка намеренная!
            "refresh": str(refresh),
        })
```

---

## Soft Delete в ViewSet

```python
class BaseViewSet(viewsets.ModelViewSet):
    """
    Базовый ViewSet: destroy → soft_delete вместо hard delete.
    Наследуй от него все ViewSet'ы проекта.
    """
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.soft_delete()
        return Response(status=204)

    def get_queryset(self):
        # Возвращает только не-удалённые записи
        return super().get_queryset().filter(deleted_at__isnull=True)
```

---

## Email Validator

```python
# apps/common/validators.py
from django.core.exceptions import ValidationError


def validate_oshsu_email(value: str):
    if not value.lower().endswith("@oshsu.kg"):
        raise ValidationError("Email должен заканчиваться на @oshsu.kg")
```

---

## File Upload Validator

```python
# apps/common/validators.py
ALLOWED_EXTENSIONS = {".pdf", ".docx", ".jpg", ".jpeg", ".png"}
MAX_FILE_SIZE_MB   = 50


def validate_upload(file):
    import os
    ext = os.path.splitext(file.name)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValidationError(f"Разрешены только: {', '.join(ALLOWED_EXTENSIONS)}")
    if file.size > MAX_FILE_SIZE_MB * 1024 * 1024:
        raise ValidationError(f"Максимальный размер файла: {MAX_FILE_SIZE_MB} МБ")
```

---

## HTTP коды — шпаргалка

| Ситуация | Код |
|----------|-----|
| Список / детали | 200 |
| Создан | 201 |
| Удалён (soft) | 204 |
| Невалидные данные | 422 |
| Не найден | 404 |
| Нет прав | 403 |
| Не аутентифицирован | 401 |
| Дубликат | 409 |
