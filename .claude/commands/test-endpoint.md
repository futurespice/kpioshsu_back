Напиши тесты для эндпоинта: $ARGUMENTS

## Обязательный набор тестов

Для каждого эндпоинта напиши тесты в следующем порядке:

### 1. Аутентификация
```python
def test_unauthenticated_returns_401(self):
    """Запрос без токена → 401"""
    response = self.client.get(self.url)
    self.assertEqual(response.status_code, 401)
```

### 2. Авторизация по ролям
```python
def test_wrong_role_returns_403(self):
    """Роль без доступа → 403"""
    self.client.force_authenticate(user=self.teacher_user)  # или другая запрещённая роль
    response = self.client.get(self.url)
    self.assertEqual(response.status_code, 403)

def test_correct_role_returns_200(self):
    """Правильная роль → 200"""
    self.client.force_authenticate(user=self.allowed_user)
    response = self.client.get(self.url)
    self.assertEqual(response.status_code, 200)
```

### 3. Формат ответа
```python
def test_list_response_format(self):
    """Список возвращает правильную структуру пагинации"""
    self.client.force_authenticate(user=self.allowed_user)
    response = self.client.get(self.url)
    self.assertIn("count", response.data)
    self.assertIn("result", response.data)      # НЕ "results"!
    self.assertIn("page", response.data)
    self.assertIn("page_size", response.data)
```

### 4. Валидация
```python
def test_invalid_data_returns_422(self):
    """Невалидные данные → 422"""
    response = self.client.post(self.url, data={}, format="json")
    self.assertEqual(response.status_code, 422)
    self.assertIn("error", response.data)

def test_valid_data_returns_201(self):
    """Валидные данные → 201"""
    response = self.client.post(self.url, data=self.valid_payload, format="json")
    self.assertEqual(response.status_code, 201)
```

### 5. Soft delete
```python
def test_deleted_object_returns_404(self):
    """Soft-удалённый объект → 404"""
    self.obj.soft_delete()
    response = self.client.get(f"{self.url}{self.obj.id}/")
    self.assertEqual(response.status_code, 404)

def test_hard_delete_not_called(self):
    """Объект не удаляется из БД при DELETE-запросе"""
    self.client.force_authenticate(user=self.admin_user)
    self.client.delete(f"{self.url}{self.obj.id}/")
    # Должен существовать в all_objects
    self.assertTrue(
        MyModel.all_objects.filter(id=self.obj.id).exists()
    )
```

### 6. Специфичные для КПЭ (если применимо)
```python
def test_kpi_weight_sum_exceeds_1_returns_400(self):
    """Сумма весов > 1.0 → ошибка валидации"""
    # создать показатели с суммой 0.9, потом добавить 0.2
    ...

def test_kpi_calculation_no_division_by_zero(self):
    """Расчёт КПЭ при отсутствии показателей не падает"""
    response = self.client.get(f"/api/kpi/result/teacher/{self.teacher.id}/")
    self.assertEqual(response.status_code, 200)
    self.assertEqual(response.data["total_value"], "0.00")
```

## Структура setUp

```python
class <EndpointName>TestCase(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = "/api/<path>/"

        # Создавай по одному юзеру каждой роли, которая фигурирует в тесте
        self.admin_user     = User.objects.create_user(role=Role.ADMIN, ...)
        self.allowed_user   = User.objects.create_user(role=Role.<ALLOWED_ROLE>, ...)
        self.forbidden_user = User.objects.create_user(role=Role.<FORBIDDEN_ROLE>, ...)

        self.valid_payload = { ... }  # минимально валидный набор полей
```

## Чего НЕ делать
- Не писать тесты только для happy path
- Не мокировать то, что можно создать через ORM
- Не добавлять тесты для эндпоинтов, которые не входят в $ARGUMENTS
