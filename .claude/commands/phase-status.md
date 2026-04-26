Проверь статус реализации по фазам из ТЗ.

## Как проверять

Для каждого эндпоинта из списка ниже — выполни grep и определи статус:
- ✅ **Реализован** — найден view + url + тест
- 🔧 **Частично** — есть view, но нет тестов или url
- ❌ **Не реализован** — файлы не найдены

```bash
# Проверка наличия эндпоинта
grep -rn "<url_path>" --include="*.py" . | grep -E "url|path|router"

# Проверка наличия вьюхи
grep -rn "<ViewSetName>\|<view_name>" --include="*.py" apps/

# Проверка наличия тестов
grep -rn "<url_path>" --include="*.py" . | grep test
```

---

## Фаза 1 — Критичная (Sprint 1–2)

| Эндпоинт | Статус |
|----------|--------|
| POST /api/auth/login | |
| POST /api/auth/refresh | |
| POST /api/auth/logout | |
| GET /api/auth/me | |
| GET/POST /api/faculties | |
| GET/POST /api/departments | |
| GET/POST/PUT/DELETE /api/users | |
| POST /api/kpi | |
| GET /api/kpi | |
| PUT /api/kpi/{id} | |
| DELETE /api/kpi/{id} | |
| POST /api/kpi/value | |
| GET /api/kpi/value/{userId} | |
| GET /api/kpi/result/teacher/{id} | |
| POST/GET /api/tasks | |
| PATCH /api/tasks/{id}/status | |

## Фаза 2 — Важная (Sprint 3–4)

| Эндпоинт | Статус |
|----------|--------|
| GET/POST /api/publications | |
| GET/POST /api/documents | |
| POST /api/approvals | |
| PATCH /api/approvals/{id}/approve | |
| PATCH /api/approvals/{id}/reject | |
| GET /api/analytics/university/* | |
| GET /api/analytics/vice-rector/* | |
| GET /api/kpi/result/department/{id} | |
| GET /api/kpi/result/faculty/{id} | |
| GET /api/kpi/result/university | |

## Фаза 3 — Дополнительная (Sprint 5+)

| Эндпоинт | Статус |
|----------|--------|
| GET/POST /api/planerka | |
| DELETE /api/planerka/{id} | |
| GET/PUT /api/load/departments | |
| GET /api/analytics/dean/* | |

---

## Итог

После проверки выведи:

```
## Статус реализации

Фаза 1: X/16 эндпоинтов (XX%)
Фаза 2: X/10 эндпоинтов (XX%)
Фаза 3: X/7 эндпоинтов (XX%)

Следующий приоритет: [список нереализованных из Фазы 1]
```
