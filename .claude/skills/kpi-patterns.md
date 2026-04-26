# Skill: KPI Calculation Patterns
Подробная логика расчёта КПЭ для kpioshsu_back. Читай этот файл перед реализацией
или изменением любой логики расчёта КПЭ.

---

## Формулы

```
КПЭ преподавателя = Σ(kpi_value.value × kpi.weight) / 100
КПЭ кафедры       = mean(КПЭ всех преподавателей кафедры с is_active=True)
КПЭ факультета    = mean(КПЭ всех кафедр факультета)
КПЭ университета  = mean(КПЭ всех факультетов)
```

---

## Эталонная реализация

```python
from decimal import Decimal
from django.db.models import Avg, Sum

def calculate_teacher_kpi(user_id: str, period_type: str, period_value: str) -> Decimal:
    """
    Рассчитать КПЭ преподавателя за период.
    Возвращает Decimal(5,2), диапазон 0.00–100.00.
    """
    values = KPIValue.objects.filter(
        user_id=user_id,
        period_type=period_type,
        period_value=period_value,
        kpi__is_active=True,
    ).select_related("kpi")

    if not values.exists():
        return Decimal("0.00")  # Guard: нет данных → не падаем

    total = sum(v.value * v.kpi.weight for v in values)
    result = total / Decimal("100")

    return result.quantize(Decimal("0.01"))


def calculate_department_kpi(department_id: str, period_type: str, period_value: str):
    """
    КПЭ кафедры = среднее КПЭ активных преподавателей.
    Возвращает Decimal или None (если нет преподавателей).
    """
    teachers = User.objects.filter(
        department_id=department_id,
        role=Role.TEACHER,
        is_active=True,
        deleted_at__isnull=True,
    )

    if not teachers.exists():
        return None  # Не 0 — отсутствие данных ≠ нулевой КПЭ

    kpis = [
        calculate_teacher_kpi(t.id, period_type, period_value)
        for t in teachers
    ]

    avg = sum(kpis) / len(kpis)
    return avg.quantize(Decimal("0.01"))
```

---

## Критические edge cases

| Ситуация | Неправильно | Правильно |
|----------|-------------|-----------|
| Нет KPI-значений у преподавателя | `ZeroDivisionError` | `return Decimal("0.00")` |
| Нет преподавателей на кафедре | `return Decimal("0.00")` | `return None` |
| `total_weight = 0` (все деактивированы) | деление на ноль | `return Decimal("0.00")` |
| КПЭ > 100 из-за ошибки данных | вернуть как есть | `min(result, Decimal("100.00"))` |

---

## Валидация весов при сохранении

```python
class KPISerializer(serializers.ModelSerializer):
    def validate_weight(self, value):
        instance_id = self.instance.id if self.instance else None
        current_sum = (
            KPI.objects.filter(is_active=True)
               .exclude(id=instance_id)
               .aggregate(total=Sum("weight"))["total"]
            or Decimal("0")
        )
        if current_sum + Decimal(str(value)) > Decimal("1.0"):
            raise serializers.ValidationError(
                f"Сумма весов превысит 1.0. Доступно: {1.0 - float(current_sum):.4f}"
            )
        return value
```

---

## Модели периодов

```python
# period_type: "month" | "semester" | "year"
# period_value примеры:
#   month:    "2026-04"
#   semester: "2025-2"   (год-номер семестра)
#   year:     "2025-2026"

# Фильтрация по периоду:
KPIValue.objects.filter(
    period_type="month",
    period_value="2026-04",
)
```

---

## Хранение истории

Результаты расчёта сохраняются в `KPIResult`. При повторном расчёте за тот же период —
создаётся новая запись (не перезаписывается старая). История должна быть полной.

```python
KPIResult.objects.create(
    user=teacher,
    total_value=result,
    period_type=period_type,
    period_value=period_value,
    calculated_at=timezone.now(),
)
```
