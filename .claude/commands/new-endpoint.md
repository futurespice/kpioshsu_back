Создай полный DRF endpoint для: $ARGUMENTS

## Шаги (выполняй по порядку, каждый верифицируй)

1. **Model** → verify: файл `models.py` содержит новую модель с UUID PK и soft delete
2. **Serializer** → verify: все обязательные поля из ТЗ присутствуют
3. **ViewSet** → verify: permissions соответствуют ТЗ для каждого action
4. **URLs** → verify: эндпоинт зарегистрирован в `urls.py`
5. **Migration** → verify: `python manage.py makemigrations` проходит без ошибок
6. **Tests** → verify: тесты для 401, 403, 200/201, 422, 404 написаны и зелёные

## Обязательные правила

### Модель
```python
import uuid
from django.db import models
from django.utils import timezone

class SoftDeleteManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(deleted_at__isnull=True)

class BaseModel(models.Model):
    id         = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True, default=None)

    objects     = SoftDeleteManager()
    all_objects = models.Manager()

    def soft_delete(self):
        self.deleted_at = timezone.now()
        self.save(update_fields=['deleted_at'])

    class Meta:
        abstract = True
```

### Permissions — используй только эти роли
```python
from apps.users.models import Role

ADMIN         = Role.ADMIN          # 0
RECTOR        = Role.RECTOR         # 1
VICE_RECTOR   = Role.VICE_RECTOR    # 2
DEAN          = Role.DEAN           # 5
HEAD_OF_DEPT  = Role.HEAD_OF_DEPT   # 6
TEACHER       = Role.TEACHER        # 7
```

### Response format — ОБЯЗАТЕЛЬНО
```python
# Для списков — кастомный пагинатор, не стандартный DRF
# Ключ "result" (не "results"!)
{
    "count": N,
    "page": 1,
    "page_size": 20,
    "next": "...",
    "previous": null,
    "result": [...]
}

# Для ошибок
{"error": "...", "code": "ERROR_CODE", "details": {}}
```

### Auth endpoint — КРИТИЧНО
Если создаёшь `/auth/` — ответ должен содержать `"acces"` (без второй 's'):
```python
return Response({"acces": str(access), "refresh": str(refresh)})
# НЕ "access" — фронтенд сломается молча!
```

## Чего НЕ делать
- Не добавлять поля/логику, которых нет в ТЗ для этого эндпоинта
- Не рефакторить соседние модели или вьюхи
- Не использовать hard delete (`.delete()`) — только `.soft_delete()`
