Создай Django модель для: $ARGUMENTS

## Чеклист (проверь каждый пункт перед завершением)

- [ ] UUID primary key (`default=uuid.uuid4, editable=False`)
- [ ] `created_at` / `updated_at` (auto)
- [ ] `deleted_at = models.DateTimeField(null=True, blank=True, default=None)`
- [ ] `SoftDeleteManager` как `objects` (фильтрует `deleted_at__isnull=True`)
- [ ] `models.Manager()` как `all_objects` (включая удалённые)
- [ ] Метод `soft_delete()` вместо `.delete()`
- [ ] `__str__` возвращает человекочитаемое имя
- [ ] `class Meta` с `verbose_name` / `verbose_name_plural` на русском
- [ ] Миграция создаётся без ошибок

## Шаблон

```python
import uuid
from django.db import models
from django.utils import timezone


class SoftDeleteManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(deleted_at__isnull=True)


class <ModelName>(models.Model):
    id         = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # --- твои поля здесь ---
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True, default=None)

    objects     = SoftDeleteManager()
    all_objects = models.Manager()

    def soft_delete(self):
        self.deleted_at = timezone.now()
        self.save(update_fields=['deleted_at'])

    def __str__(self):
        return f"<ModelName> #{self.id}"

    class Meta:
        verbose_name        = "<название>"
        verbose_name_plural = "<названия>"
        ordering            = ["-created_at"]
```

## Дополнительные проверки для специфичных моделей

### Если модель содержит email
```python
# Валидация домена @oshsu.kg
def clean(self):
    if self.email and not self.email.endswith("@oshsu.kg"):
        raise ValidationError({"email": "Email должен заканчиваться на @oshsu.kg"})
```

### Если модель содержит КПЭ-вес
```python
# Валидация суммы весов
def clean(self):
    from django.db.models import Sum
    current_sum = KPI.objects.filter(is_active=True).exclude(id=self.id) \
                             .aggregate(total=Sum('weight'))['total'] or 0
    if current_sum + self.weight > 1.0:
        raise ValidationError({"weight": "Сумма весов показателей превышает 1.0"})
```

### Если модель содержит deadline
```python
from django.utils import timezone

def clean(self):
    if self.deadline and self.deadline < timezone.now().date():
        raise ValidationError({"deadline": "Дедлайн не может быть в прошлом"})
```

## Чего НЕ делать
- Не переопределять `.delete()` — только добавлять `.soft_delete()`
- Не трогать соседние модели в файле
- Не добавлять поля, которых нет в ТЗ для этой сущности
