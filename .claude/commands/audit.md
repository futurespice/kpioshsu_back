Проведи аудит кода проекта на предмет критических анти-паттернов.

## Чеклист аудита

Пройди по каждому пункту. Для каждой найденной проблемы — укажи файл, строку и способ исправления.

---

### 🔴 Критично (баги в production)

**1. Опечатка в ключе токена**
```bash
# Ищи "access" в auth-ответах — должно быть "acces"
grep -rn '"access"' --include="*.py" .
grep -rn "'access'" --include="*.py" .
```
Ожидаемый ответ: `{"acces": "...", "refresh": "..."}` — без второй 's'

**2. Hard delete вместо soft delete**
```bash
# Ищи прямые вызовы .delete() на моделях данных
grep -rn "\.delete()" --include="*.py" . | grep -v "test_" | grep -v "migrations"
```
Все модели должны использовать `.soft_delete()`, а не `.delete()`

**3. Деление на ноль в расчёте КПЭ**
```bash
grep -rn "total_weight\|sum.*weight\|/ 100\|/ len" --include="*.py" .
```
Проверь: есть ли guard `if total_weight == 0: return Decimal("0.00")`

**4. Отсутствие валидации суммы весов КПЭ**
```bash
grep -rn "weight" apps/kpi/serializers.py apps/kpi/models.py
```
Должна быть проверка: `Σ активных весов + new_weight <= 1.0`

---

### 🟡 Важно (неправильное поведение)

**5. Неправильный ключ пагинации**
```bash
grep -rn '"results"' --include="*.py" . | grep -v "test_"
```
Должно быть `"result"` (без 's') — так ждёт фронтенд

**6. Email валидация без проверки домена**
```bash
grep -rn "email" apps/users/serializers.py apps/users/models.py
```
Должна быть проверка `endswith("@oshsu.kg")`

**7. Дедлайн в прошлом при создании задачи**
```bash
grep -rn "deadline" apps/tasks/serializers.py
```
Должна быть проверка `deadline >= today`

**8. Файлы без проверки размера и формата**
```bash
grep -rn "FileField\|ImageField\|upload" --include="*.py" .
```
Максимум 50 МБ, форматы: PDF, DOCX, JPG, PNG

---

### 🟢 Проверки качества

**9. Отсутствие `deleted_at` у новых моделей**
```bash
grep -rn "class.*Model" --include="*.py" apps/ | grep -v "Abstract\|Base\|Migration"
```
Каждая модель должна наследовать BaseModel или иметь `deleted_at`

**10. CORS не настроен**
```bash
grep -rn "CORS" config/settings*.py
```
Должны быть `CORS_ALLOWED_ORIGINS` и `CORS_ALLOW_HEADERS`

**11. Rate limiting отсутствует**
```bash
grep -rn "throttle\|rate" config/settings*.py
```
Должно быть: `DEFAULT_THROTTLE_RATES = {"anon": "100/min"}`

---

## Формат отчёта

После проверки выведи:

```
## Результаты аудита

### 🔴 Критичные проблемы (N)
- [файл:строка] Описание → Как исправить

### 🟡 Важные проблемы (N)
- [файл:строка] Описание → Как исправить

### 🟢 Качество (N)
- [файл:строка] Описание → Как исправить

### ✅ Всё ок (N пунктов прошли проверку)
```

Не исправляй ничего автоматически — только докладывай. Исправления — по отдельному запросу.
