ОШСКИЙ ГОСУДАРСТВЕННЫЙ УНИВЕРСИТЕТ
Информационная система анализа КПЭ и архивации УМК

ТЕХНИЧЕСКОЕ ЗАДАНИЕ
для Back-End разработчика


Версия 1.0
Апрель 2026



| Система | kpi_oshsu — ИС анализа КПЭ образовательной деятельности |
| --- | --- |
| Версия документа | 1.0 |
| Дата | Апрель 2026 |
| Составил | Frontend-разработчик (на основе анализа исходного кода) |
| Назначение | Руководство для разработки REST API backend-части системы |
| Технологический стек Frontend | React 19, TypeScript, Vite, Zustand, Axios, Recharts |
| Аутентификация | JWT (access + refresh tokens) |
| Базовый URL API | VITE_API_BACKEND_URL (настраивается в .env) |


# 1. Общие сведения
## 1.1 Назначение документа
Данное техническое задание (ТЗ) описывает требования к разработке серверной части (back-end) информационной системы анализа ключевых показателей эффективности (КПЭ) образовательной деятельности и архивации учебно-методических комплексов (УМК) для Ошского государственного университета.
ТЗ составлено на основе анализа исходного кода front-end приложения (React + TypeScript) и является исчерпывающим руководством для back-end разработчика.
## 1.2 Цель системы
Система предназначена для:
мониторинга и расчёта КПЭ преподавателей, кафедр, факультетов и университета в целом;
управления задачами в иерархии: Ректор → Проректор → Декан → Завкафедрой → Преподаватель;
хранения и согласования документов (рабочие программы, методические указания, УМК, силлабусы);
архивации и учёта научных публикаций преподавателей;
разграничения доступа по ролям пользователей.
## 1.3 Рекомендуемый технологический стек

| Backend framework | Django REST Framework (Python) или NestJS (Node.js/TypeScript) |
| --- | --- |
| База данных | PostgreSQL 15+ |
| ORM | SQLAlchemy / Django ORM (Python) или Prisma / TypeORM (Node.js) |
| Аутентификация | JWT (SimpleJWT для Django, @nestjs/jwt для NestJS) |
| Хранение файлов | AWS S3 / MinIO / локальное хранилище |
| Документация API | Swagger / OpenAPI 3.0 |
| Кэширование | Redis (опционально, для аналитики) |
| Контейнеризация | Docker + Docker Compose |


# 2. Роли пользователей
Фронтенд использует следующий enum ролей (файл src/shared/lib/types/types.ts):


| # | Роль (enum ROLES) | Описание и маршрут в системе |
| --- | --- | --- |
| 0 | ADMIN | Системный администратор. Управление пользователями, конфигурация |
| 1 | RECTOR | Ректор. Стратегический контроль, постановка задач проректорам. /dashboard/rector |
| 2 | VICE_RECTOR | Проректор. Согласование УМК/отчётов, маршрутизация задач, планёрки. /dashboard/vice-rector |
| 3 | SCIENCE_DEP | Научно-исследовательский отдел. Мониторинг публикаций. /dashboard/science |
| 4 | STUDENT_AFFAIRS | Студенческий отдел. /dashboard/student-affairs |
| 5 | DEAN | Декан факультета. Управление кафедрами, назначение задач. /dashboard/dean |
| 6 | HEAD_OF_DEPT | Завкафедрой. Постановка задач преподавателям. /dashboard/head-of-dept |
| 7 | TEACHER | Преподаватель. Задачи, публикации, документы, КПЭ. /dashboard/teacher |


# 3. Аутентификация и авторизация
## 3.1 Механизм аутентификации
Фронтенд использует JWT-аутентификацию. Анализ файла src/shared/lib/axios/API.ts:
Access token сохраняется в localStorage под ключом "acces" (с опечаткой — так и реализовано во фронтенде)
Refresh token сохраняется в localStorage под ключом "refresh"
При 401 ответе автоматически вызывается POST /auth/refresh с передачей refresh token в теле запроса
После обновления токены перезаписываются в localStorage
Access token передаётся в заголовке: Authorization: Bearer <token>

## 3.2 Эндпоинты аутентификации

| Метод | URL | Доступ | Описание |
| --- | --- | --- | --- |
| POST | /api/auth/login | Публичный | Вход по email и паролю. Возвращает access + refresh tokens |
| POST | /api/auth/refresh | Публичный | Обновление токенов. Body: { token: string }. Возвращает { acces: string, refresh: string } |
| POST | /api/auth/logout | JWT | Инвалидация refresh token (занести в blacklist) |
| GET | /api/auth/me | JWT | Получить профиль текущего пользователя с ролью |


## 3.3 Формат запроса и ответа
POST /api/auth/login — Request Body:
{ "login": "user@oshsu.kg", "password": "string" }
POST /api/auth/login — Response 200:
{ "acces": "eyJ...", "refresh": "eyJ..." }
ВАЖНО: ключ поля access token в ответе должен быть "acces" (без буквы 's') — именно так написано во фронтенде в API.ts interceptor.

## 3.4 Модель пользователя

| Поле | Тип | Обязательное | Описание |
| --- | --- | --- | --- |
| id | UUID / BigInt | Да | Первичный ключ |
| full_name | VARCHAR(255) | Да | Полное имя сотрудника |
| email | VARCHAR(255) | Да | Корпоративная почта @oshsu.kg (используется как login) |
| password_hash | VARCHAR(255) | Да | Хэш пароля (bcrypt) |
| role | ENUM(ROLES) | Да | Роль пользователя: 0-7 согласно enum |
| department_id | FK -> Department | Нет | Кафедра/подразделение |
| faculty_id | FK -> Faculty | Нет | Факультет |
| is_active | BOOLEAN | Да | Активен ли аккаунт (default: true) |
| created_at | TIMESTAMP | Да | Дата создания |
| updated_at | TIMESTAMP | Да | Дата обновления |


# 4. Модуль КПЭ (Key Performance Indicators)
## 4.1 Бизнес-логика расчёта
Формула расчёта КПЭ преподавателя (из файла TeacherMain.tsx):
КПЭ = (П₁ × В₁ + П₂ × В₂ + П₃ × В₃) / 100
где Пₙ — значение показателя (0–100), Вₙ — вес показателя (0.0–1.0).
⚠️  ВАЖНО — НЕСООТВЕТСТВИЕ ФОРМУЛЫ (требует согласования с фронтом): При value ∈ [0, 100] и weight ∈ [0, 1] результат формулы (П×В)/100 даёт диапазон [0, 1], а не [0, 100]. Два варианта реализации:
Если итог должен быть в [0, 100]: КПЭ = Σ(valueᵢ × weightᵢ) — без деления на 100. Сумма весов должна быть = 1.0.
Если деление на 100 нужно — тогда value должен быть в диапазоне [0, 10000] (что нелогично).
РЕКОМЕНДАЦИЯ: реализовать вариант 1 — КПЭ = Σ(valueᵢ × weightᵢ), результат в диапазоне [0, 100]. Согласовать с фронтенд-разработчиком до начала интеграции.
КПЭ кафедры = среднее арифметическое КПЭ всех преподавателей кафедры.
КПЭ факультета = среднее арифметическое КПЭ всех кафедр факультета.
КПЭ университета = среднее арифметическое КПЭ всех факультетов.

## 4.2 Модели данных КПЭ
Таблица KPI (показатели):

| Поле | Тип | Обязательное | Описание |
| --- | --- | --- | --- |
| id | UUID | Да | Первичный ключ |
| name | VARCHAR(255) | Да | Название показателя |
| description | TEXT | Нет | Описание показателя |
| weight | DECIMAL(5,4) | Да | Вес показателя (0.0000–1.0000). Сумма весов <= 1.0 |
| is_active | BOOLEAN | Да | Активен ли показатель |
| created_by | FK -> User | Да | Кто создал (ADMIN/HEAD_OF_DEPT) |
| created_at | TIMESTAMP | Да | Дата создания |


Таблица KPI_Value (значения показателей):

| Поле | Тип | Обязательное | Описание |
| --- | --- | --- | --- |
| id | UUID | Да | Первичный ключ |
| user_id | FK -> User | Да | Преподаватель |
| kpi_id | FK -> KPI | Да | Показатель КПЭ |
| value | DECIMAL(5,2) | Да | Значение от 0 до 100 |
| period_type | ENUM(month/semester/year) | Да | Тип периода |
| period_value | VARCHAR(20) | Да | Значение периода: '2026-02', '2025-2', '2025-2026' |
| created_at | TIMESTAMP | Да | Дата заполнения |


Таблица KPI_Result (итоговые результаты):

| Поле | Тип | Обязательное | Описание |
| --- | --- | --- | --- |
| id | UUID | Да | Первичный ключ |
| user_id | FK -> User | Да | Преподаватель |
| total_value | DECIMAL(5,2) | Да | Итоговый КПЭ (0–100) |
| period_type | ENUM | Да | Тип периода |
| period_value | VARCHAR(20) | Да | Период |
| calculated_at | TIMESTAMP | Да | Дата расчёта |

ℹ️  ТРИГГЕР ЗАПИСИ KPI_Result: Запись в KPI_Result создаётся / перезаписывается при каждом вызове POST /api/kpi/value (фаза 1). Таблица готова, но GET-эндпоинт аналитики читает из неё, а не пересчитывает на лету. Это разгружает аналитику на фазе 2.

## 4.3 API эндпоинты КПЭ

| Метод | URL | Доступ | Описание |
| --- | --- | --- | --- |
| POST | /api/kpi | ADMIN / HEAD_OF_DEPT | Создать показатель КПЭ |
| GET | /api/kpi | Authenticated | Список активных показателей |
| PUT | /api/kpi/{id} | ADMIN / HEAD_OF_DEPT | Редактировать показатель |
| DELETE | /api/kpi/{id} | ADMIN | Деактивировать показатель (soft delete) |
| POST | /api/kpi/value | HEAD_OF_DEPT / ADMIN | Внести значение КПЭ для преподавателя |
| GET | /api/kpi/value/{userId} | Authenticated | Значения КПЭ пользователя по периодам |
| GET | /api/kpi/result/teacher/{id} | Authenticated | Итоговый КПЭ преподавателя |
| GET | /api/kpi/result/department/{id} | DEAN / HEAD_OF_DEPT | КПЭ кафедры |
| GET | /api/kpi/result/faculty/{id} | RECTOR / VICE_RECTOR / DEAN | КПЭ факультета |
| GET | /api/kpi/result/university | RECTOR / VICE_RECTOR | КПЭ университета (агрегированный) |


# 5. Модуль задач (Task Management)
## 5.1 Иерархия задач
Анализ фронтенда выявил следующую цепочку постановки задач:


| От кого | Кому | Описание |
| --- | --- | --- |
| Ректор (RECTOR) | Проректор (VICE_RECTOR) | Стратегические задачи по факультетам с приоритетом и дедлайном |
| Проректор (VICE_RECTOR) | Декан (DEAN) | Маршрутизация задач ректора, собственные задачи |
| Декан (DEAN) | Завкафедрой / Преподаватель | Назначение задач кафедре или конкретному преподавателю |
| Завкафедрой (HEAD_OF_DEPT) | Преподаватель (TEACHER) | Персональные задачи преподавателю (fromHead = true) |


## 5.2 Модель задачи

| Поле | Тип | Обязательное | Описание |
| --- | --- | --- | --- |
| id | UUID / BigInt | Да | Первичный ключ |
| title | VARCHAR(500) | Да | Название задачи |
| description | TEXT | Нет | Подробное описание |
| priority | ENUM(high/medium/low) | Да | Приоритет |
| status | ENUM(pending/in_progress/completed/routed) | Да | Статус задачи |
| points | INT | Да | Количество баллов КПЭ за выполнение |
| deadline | DATE | Да | Срок выполнения |
| from_user_id | FK -> User | Да | Автор задачи |
| to_user_id | FK -> User | Нет | Исполнитель (конкретный пользователь) |
| to_dept_id | FK -> Department | Нет | Целевая кафедра (если задача кафедре) |
| faculty_id | FK -> Faculty | Нет | Целевой факультет |
| routed_to | VARCHAR(255) | Нет | Кому перенаправлено (имя/должность) |
| routed_at | TIMESTAMP | Нет | Когда перенаправлено |
| hours | INT | Нет | Трудоёмкость в часах (используется в нагрузке) |
| created_at | TIMESTAMP | Да | Дата создания |
| updated_at | TIMESTAMP | Да | Дата обновления |


## 5.3 API эндпоинты задач

| Метод | URL | Доступ | Описание |
| --- | --- | --- | --- |
| POST | /api/tasks | RECTOR, VICE_RECTOR, DEAN, HEAD_OF_DEPT | Создать задачу |
| GET | /api/tasks | Authenticated | Список задач. Query: ?status=&priority=&from_user=&to_user= |
| GET | /api/tasks/my | Authenticated | Входящие задачи текущего пользователя |
| GET | /api/tasks/outgoing | Authenticated | Исходящие задачи текущего пользователя |
| PUT | /api/tasks/{id} | Owner / Admin | Редактировать задачу |
| PATCH | /api/tasks/{id}/status | Assigned User | Обновить статус: pending/in_progress/completed |
| PATCH | /api/tasks/{id}/route | VICE_RECTOR | Маршрутизировать задачу: { destination: string } |
| DELETE | /api/tasks/{id} | Owner / Admin | Удалить задачу (soft delete) |


# 6. Модуль публикаций (Научные статьи)
## 6.1 Описание
Реализован в компоненте ArticlesBlock.tsx. Преподаватель ведёт учёт своих научных публикаций. Каждая публикация добавляет баллы к КПЭ в зависимости от типа журнала.

## 6.2 Типы журналов и баллы КПЭ

| ID | Название | Баллы КПЭ | Описание |
| --- | --- | --- | --- |
| scopus | Scopus | 25 баллов | Международная база цитирования |
| wos | WoS (Web of Science) | 25 баллов | Международная база цитирования |
| vak | ВАК | 15 баллов | Высшая аттестационная комиссия |
| rinc | РИНЦ | 8 баллов | Российский индекс научного цитирования |
| other | Прочее | 3 баллов | Прочие издания |


## 6.3 Модель публикации

| Поле | Тип | Обязательное | Описание |
| --- | --- | --- | --- |
| id | UUID | Да | Первичный ключ |
| user_id | FK -> User | Да | Автор публикации |
| title | VARCHAR(1000) | Да | Название статьи |
| journal | VARCHAR(500) | Нет | Название журнала/сборника |
| journal_type | ENUM(scopus/wos/vak/rinc/other) | Да | Тип издания |
| pub_date | DATE | Да | Дата публикации |
| url | VARCHAR(2048) | Нет | Ссылка на статью |
| coauthors | TEXT | Нет | Список соавторов |
| kpi_indicator_id | FK -> KPI | Нет | Привязка к KPI-показателю |
| evidence_file | VARCHAR(500) | Нет | Путь к подтверждающему документу (PDF/JPG) |
| is_archived | BOOLEAN | Да | В архиве (прошлые учебные годы) |
| academic_year | VARCHAR(10) | Да | Учебный год: '2025-2026' |
| created_at | TIMESTAMP | Да | Дата добавления |


## 6.4 API эндпоинты публикаций

| Метод | URL | Доступ | Описание |
| --- | --- | --- | --- |
| POST | /api/publications | TEACHER | Добавить публикацию. Поддерживает multipart/form-data для загрузки файла |
| GET | /api/publications | Authenticated | Список публикаций. Query: ?user_id=&year=&type=&archived= |
| GET | /api/publications/my | TEACHER | Мои публикации с разбивкой по учебным годам |
| GET | /api/publications/{id} | Authenticated | Получить публикацию по ID |
| PUT | /api/publications/{id} | Owner / ADMIN | Редактировать публикацию |
| DELETE | /api/publications/{id} | Owner / ADMIN | Удалить публикацию |
| GET | /api/publications/stats/{userId} | Authenticated | Статистика публикаций: кол-во по типам, сумма КПЭ |


# 7. Модуль документов и УМК
## 7.1 Описание
Документы (рабочие программы, методические указания, силлабусы, УМК) проходят цепочку согласования: Кафедра → Декан → Ректор. Реализовано в DocumentsBlock.tsx и ViceRectorDashboard (ApprovalsPanel).

## 7.2 Типы документов
umk — Учебно-методический комплекс
report — Отчёт (воспитательная работа, НИО и др.)
syllabus — Силлабус дисциплины
work_program — Рабочая программа дисциплины
method_guide — Методические указания

## 7.3 Модель документа

| Поле | Тип | Обязательное | Описание |
| --- | --- | --- | --- |
| id | UUID | Да | Первичный ключ |
| title | VARCHAR(500) | Да | Название документа |
| doc_type | ENUM(umk/report/syllabus/work_program/method_guide) | Да | Тип документа |
| user_id | FK -> User | Да | Загрузивший преподаватель |
| department_id | FK -> Department | Да | Кафедра |
| file_path | VARCHAR(1000) | Да | Путь к файлу в хранилище |
| file_size | INT | Нет | Размер файла в байтах |
| mime_type | VARCHAR(100) | Нет | MIME-тип файла |
| status | ENUM(pending/approved/rejected) | Да | Статус документа |
| approved_by_dept | BOOLEAN | Да | Согласовано кафедрой |
| approved_by_dean | BOOLEAN | Да | Согласовано деканом |
| approved_by_rector | BOOLEAN | Да | Согласовано ректором (через проректора) |
| approved_at | TIMESTAMP | Нет | Дата финального согласования |
| academic_year | VARCHAR(10) | Да | Учебный год |
| created_at | TIMESTAMP | Да | Дата загрузки |


## 7.4 API эндпоинты документов

| Метод | URL | Доступ | Описание |
| --- | --- | --- | --- |
| POST | /api/documents | TEACHER / HEAD_OF_DEPT | Загрузить документ (multipart/form-data) |
| GET | /api/documents | Authenticated | Список документов. Query: ?dept_id=&type=&status=&year= |
| GET | /api/documents/{id} | Authenticated | Получить документ по ID |
| PATCH | /api/documents/{id}/approve | DEAN / VICE_RECTOR / RECTOR | Согласовать документ. Body: { level: 'dept'|'dean'|'rector' } |
| PATCH | /api/documents/{id}/reject | DEAN / VICE_RECTOR / RECTOR | Отклонить документ. Body: { reason: string } |
| DELETE | /api/documents/{id} | Owner / ADMIN | Удалить документ |
| GET | /api/documents/{id}/download | Authenticated | Скачать файл документа |
| GET | /api/documents/umk/status | VICE_RECTOR / RECTOR | Сводный статус УМК по кафедрам |


# 8. Модуль структуры университета
## 8.1 Сущности
Из анализа данных фронтенда выявлены следующие сущности структуры:

Таблица Faculty (Факультеты):

| Поле | Тип | Обязательное | Описание |
| --- | --- | --- | --- |
| id | UUID | Да | Первичный ключ |
| name | VARCHAR(255) | Да | Полное название: 'Инженерный факультет' |
| short_name | VARCHAR(20) | Нет | Краткое название: 'eng' |
| dean_id | FK -> User | Нет | Декан факультета |
| is_active | BOOLEAN | Да | Активен ли факультет |


Таблица Department (Кафедры):

| Поле | Тип | Обязательное | Описание |
| --- | --- | --- | --- |
| id | UUID | Да | Первичный ключ |
| name | VARCHAR(255) | Да | Полное название: 'Кафедра информатики' |
| short | VARCHAR(10) | Нет | Аббревиатура: 'ИТ', 'МАТ' |
| faculty_id | FK -> Faculty | Да | Принадлежность к факультету |
| head_id | FK -> User | Нет | Завкафедрой |
| teacher_count | INT | Нет | Кол-во преподавателей (вычисляемое) |
| target_hours | INT | Нет | Плановая нагрузка в часах |


## 8.2 API структуры

| Метод | URL | Доступ | Описание |
| --- | --- | --- | --- |
| GET | /api/faculties | Authenticated | Список факультетов |
| GET | /api/faculties/{id} | Authenticated | Факультет с кафедрами и статистикой |
| GET | /api/departments | Authenticated | Список кафедр. Query: ?faculty_id= |
| GET | /api/departments/{id} | Authenticated | Кафедра с преподавателями и КПЭ |
| GET | /api/departments/{id}/load | DEAN / VICE_RECTOR | Нагрузка кафедры: часы, процент выполнения |
| GET | /api/users | ADMIN / RECTOR / VICE_RECTOR / DEAN | Список пользователей. Query: ?role=&dept_id=&faculty_id= |
| GET | /api/users/{id} | Authenticated | Профиль пользователя |
| POST | /api/users | ADMIN | Создать пользователя |
| PUT | /api/users/{id} | ADMIN | Редактировать пользователя |


# 9. Модуль аналитики (Дашборды)
## 9.1 Данные для дашборда Ректора
Из RectorDashboard.tsx выявлены следующие данные, которые должен отдавать API:

| Метод | URL | Доступ | Описание |
| --- | --- | --- | --- |
| GET | /api/analytics/university/overview | RECTOR / VICE_RECTOR | Общий КПЭ, кол-во преподавателей, публикаций, грантов, программ |
| GET | /api/analytics/university/kpi-trend | RECTOR / VICE_RECTOR | Динамика КПЭ по месяцам: [{ period, kpi }] |
| GET | /api/analytics/university/faculty-kpi | RECTOR / VICE_RECTOR | КПЭ по факультетам: [{ name, kpi, trend }] |
| GET | /api/analytics/university/radar | RECTOR / VICE_RECTOR | Профиль: [{ subject, value }] по направлениям (наука, учеб. работа и др.) |
| GET | /api/analytics/university/heatmap | RECTOR / VICE_RECTOR | Тепловая карта КПЭ по факультетам/месяцам |
| GET | /api/analytics/university/goals | RECTOR | Стратегические цели с прогрессом |
| GET | /api/analytics/university/alerts | RECTOR | Уведомления: аномалии, дедлайны, достижения |


## 9.2 Данные для дашборда Проректора

| Метод | URL | Доступ | Описание |
| --- | --- | --- | --- |
| GET | /api/analytics/vice-rector/overview | VICE_RECTOR | Сводка: кол-во согласований, задач, нагрузка кафедр |
| GET | /api/analytics/vice-rector/dept-load | VICE_RECTOR | Нагрузка кафедр: [{ dept, hours, target, pct }] |
| GET | /api/analytics/vice-rector/success-data | VICE_RECTOR | Успеваемость по месяцам: [{ month, сдано, ср_балл }] |
| GET | /api/analytics/vice-rector/umk-status | VICE_RECTOR | Статус УМК: [{ subject, dept, status }] |


## 9.3 Данные для дашборда Декана

| Метод | URL | Доступ | Описание |
| --- | --- | --- | --- |
| GET | /api/analytics/dean/overview | DEAN | Сводка по факультету |
| GET | /api/analytics/dean/teachers | DEAN | Список преподавателей с КПЭ, нагрузкой, публикациями, задачами |
| GET | /api/analytics/dean/departments | DEAN | Кафедры с агрегированными показателями |


# 10. Планёрка (Planerka Calendar)
## 10.1 Описание
Компонент PlanerkaCalendar.tsx в дашборде проректора. Позволяет создавать и удалять события планёрки.

## 10.2 Модель события планёрки

| Поле | Тип | Обязательное | Описание |
| --- | --- | --- | --- |
| id | UUID | Да | Первичный ключ |
| title | VARCHAR(500) | Да | Название задачи/события |
| description | TEXT | Нет | Описание |
| faculty | VARCHAR(255) | Нет | Факультет |
| priority | ENUM(high/medium/low) | Да | Приоритет |
| deadline | DATE | Да | Дата события |
| points | INT | Нет | Баллы КПЭ |
| hours | INT | Нет | Трудоёмкость в часах |
| status | VARCHAR(50) | Да | Статус события |
| created_by | FK -> User | Да | Автор (VICE_RECTOR) |
| created_at | TIMESTAMP | Да | Дата создания |



| Метод | URL | Доступ | Описание |
| --- | --- | --- | --- |
| GET | /api/planerka | VICE_RECTOR / RECTOR | Список событий планёрки |
| POST | /api/planerka | VICE_RECTOR | Создать событие |
| DELETE | /api/planerka/{id} | VICE_RECTOR | Удалить событие |


# 11. Согласования (Approvals)
## 11.1 Описание
ApprovalsPanel.tsx — панель проректора для согласования/отклонения входящих документов и отчётов.

## 11.2 Модель согласования

| Поле | Тип | Обязательное | Описание |
| --- | --- | --- | --- |
| id | UUID | Да | Первичный ключ |
| type | ENUM(umk/report/syllabus) | Да | Тип согласования |
| title | VARCHAR(500) | Да | Название |
| from_user_id | FK -> User | Да | Инициатор |
| department_id | FK -> Department | Нет | Кафедра |
| document_id | FK -> Document | Нет | Связанный документ |
| status | ENUM(pending/approved/rejected) | Да | Статус |
| submitted_at | TIMESTAMP | Да | Дата подачи |
| resolved_at | TIMESTAMP | Нет | Дата решения |
| resolved_by | FK -> User | Нет | Кто принял решение |



| Метод | URL | Доступ | Описание |
| --- | --- | --- | --- |
| GET | /api/approvals | VICE_RECTOR / RECTOR | Список согласований. Query: ?status=pending |
| PATCH | /api/approvals/{id}/approve | VICE_RECTOR / RECTOR | Одобрить |
| PATCH | /api/approvals/{id}/reject | VICE_RECTOR / RECTOR | Отклонить. Body: { reason: string } |
| POST | /api/approvals | DEAN / HEAD_OF_DEPT / TEACHER | Подать на согласование |


# 12. Нагрузка кафедр (Department Load)
## 12.1 Описание
Из DeptLoadCard и deptLoad данных в viceRector типах: каждая кафедра имеет плановую и фактическую нагрузку в часах.

## 12.2 Модель нагрузки

| Поле | Тип | Обязательное | Описание |
| --- | --- | --- | --- |
| id | UUID | Да | Первичный ключ |
| department_id | FK -> Department | Да | Кафедра |
| academic_year | VARCHAR(10) | Да | Учебный год |
| semester | INT | Да | Семестр: 1 или 2 |
| target_hours | INT | Да | Плановая нагрузка (часы) |
| actual_hours | INT | Да | Фактическая нагрузка (часы) |
| pct | DECIMAL(5,2) | Нет | Процент выполнения (вычисляемое) |
| updated_at | TIMESTAMP | Да | Дата обновления |



| Метод | URL | Доступ | Описание |
| --- | --- | --- | --- |
| GET | /api/load/departments | VICE_RECTOR / RECTOR | Нагрузка всех кафедр |
| GET | /api/load/departments/{id} | DEAN / VICE_RECTOR | Нагрузка конкретной кафедры |
| PUT | /api/load/departments/{id} | ADMIN / HEAD_OF_DEPT | Обновить нагрузку кафедры |


# 13. Контракт загрузки файлов (File Upload)
## 13.1 Механизм хранения
Клиент загружает файл напрямую в своё хранилище (S3/MinIO/CDN), затем передаёт в API только строку-путь. Бэкенд хранит путь как строку. Прямой стриминг файлов через API не требуется.

## 13.2 Поля типа «файл» и их формат

| Поле | Таблица | Описание |
| --- | --- | --- |
| evidence_file | Publication | Путь к подтверждающему документу (PDF/JPG). Строка. Клиент загружает файл сам, передаёт URL/path. |
| file_path | Document | Путь к файлу документа/УМК. Строка. Клиент загружает файл сам, передаёт URL/path. |


## 13.3 Формат передачи пути
Клиент передаёт в теле запроса (JSON):
{ "evidence_file": "https://storage.oshsu.kg/uploads/2026/doc123.pdf" }
Бэкенд сохраняет строку as-is. Валидация: строка должна быть URL или непустым путём, максимум 1000 символов.
Примечание: в компоненте SampleBlock.tsx фронтенд показывает drag-and-drop UI с принятием файлов PDF/DOCX/PNG/JPG до 20 МБ. Логика загрузки в хранилище — на стороне клиента.


# 14. Модуль экспорта
## 14.1 Описание
Экспорт данных в файлы Excel/PDF для отчётности. Раздел добавлен на основании потребностей системы — конкретный UI во фронтенде ещё не реализован, поэтому контракт согласовывается отдельно.

## 14.2 API эндпоинты экспорта

| Метод | URL | Доступ | Описание |
| --- | --- | --- | --- |
| GET | /api/export/kpi/teacher/{id} | Authenticated | Выгрузка КПЭ преподавателя за период. Query: ?period_type=&period_value=&format=xlsx|pdf |
| GET | /api/export/kpi/department/{id} | DEAN / HEAD_OF_DEPT | Выгрузка КПЭ кафедры. Query: ?year=&format=xlsx|pdf |
| GET | /api/export/kpi/faculty/{id} | RECTOR / VICE_RECTOR / DEAN | Выгрузка КПЭ факультета. Query: ?year=&format=xlsx|pdf |
| GET | /api/export/tasks | Authenticated | Экспорт задач. Query: ?status=&priority=&from=&to=&format=xlsx|pdf |
| GET | /api/export/publications/{userId} | Authenticated | Экспорт публикаций преподавателя. Query: ?year=&format=xlsx|pdf |
| GET | /api/export/report/university | RECTOR | Полный отчёт по университету. Query: ?year=&format=xlsx|pdf |


⚠️  СТАТУС: Контракт на экспорт требует отдельного согласования с фронтендом. Параметры фильтрации, структура файлов и наименования колонок уточняются. Рекомендуется реализовать в Фазе 3.


# 15. Стратегические цели, Гранты и Программы
## 15.1 Описание
Данные отображаются в дашборде Ректора (RectorDashboard.tsx): стратегические цели с прогрессом, активные гранты, аккредитованные программы. В текущей версии фронтенда данные захардкожены. Модели описаны для будущей реализации.

## 15.2 Стратегические цели

| Поле | Тип | Обязательное | Описание |
| --- | --- | --- | --- |
| id | UUID | Да | Первичный ключ |
| title | VARCHAR(500) | Да | Название цели: 'Рост публикаций в Scopus до 120 ед.' |
| current_value | DECIMAL(10,2) | Да | Текущее значение: 89 |
| target_value | DECIMAL(10,2) | Да | Целевое значение: 120 |
| unit | VARCHAR(50) | Нет | Единица измерения: 'ед.', '%', 'млн С' |
| academic_year | VARCHAR(10) | Да | Учебный год: '2025-2026' |
| is_active | BOOLEAN | Да | Активна ли цель |


## 15.3 Гранты

| Поле | Тип | Обязательное | Описание |
| --- | --- | --- | --- |
| id | UUID | Да | Первичный ключ |
| title | VARCHAR(500) | Да | Название гранта |
| amount | DECIMAL(12,2) | Да | Сумма (в сомах) |
| status | ENUM(active/completed/pending) | Да | Статус гранта |
| faculty_id | FK -> Faculty | Нет | Факультет |
| year | INT | Да | Год получения |


## 15.4 Аккредитованные программы

| Поле | Тип | Обязательное | Описание |
| --- | --- | --- | --- |
| id | UUID | Да | Первичный ключ |
| title | VARCHAR(500) | Да | Название программы |
| faculty_id | FK -> Faculty | Да | Факультет |
| status | ENUM(accredited/pending/rejected) | Да | Статус аккредитации |
| accredited_at | DATE | Нет | Дата аккредитации |
| expires_at | DATE | Нет | Срок действия аккредитации |


## 15.5 API эндпоинты

| Метод | URL | Доступ | Описание |
| --- | --- | --- | --- |
| GET | /api/strategic-goals | RECTOR / VICE_RECTOR | Список стратегических целей с прогрессом. Query: ?year= |
| PUT | /api/strategic-goals/{id} | ADMIN / RECTOR | Обновить текущее значение цели |
| GET | /api/grants | RECTOR / VICE_RECTOR | Список грантов. Query: ?year=&status= |
| GET | /api/programs | Authenticated | Список образовательных программ. Query: ?faculty_id=&status= |
| GET | /api/analytics/university/overview | RECTOR / VICE_RECTOR | Агрегат: кол-во преподавателей, публикаций, активных грантов, программ, общий КПЭ |


## 15.6 Поведение при отсутствии данных
Все аналитические эндпоинты (Grants, Programs, Strategic Goals, Exam grades) должны возвращать пустые массива [] или нулевые значения 0 при отсутствии данных — никаких 404 или 500. Фронтенд обрабатывает пустые ответы gracefully.
// Пример: GET /api/grants?year=2026 при отсутствии данных:
{ "count": "0", "page": 1, "page_size": 20, "result": [] }

## 13.1 Формат ответов
Все эндпоинты возвращают JSON. Успешный ответ со списком:
{ "count": 10, "page": 1, "page_size": 20, "next": "...", "previous": "...", "result": [...] }
Структура PaginationResult<T> соответствует интерфейсу фронтенда в interfeces.ts.
Ошибочный ответ:
{ "error": "Описание ошибки", "code": "ERROR_CODE", "details": {} }

## 13.2 HTTP коды ответов

| Код | Значение |
| --- | --- |
| 200 | OK — успешный запрос |
| 201 | Created — ресурс создан |
| 204 | No Content — успешное удаление |
| 400 | Bad Request — некорректные данные запроса |
| 401 | Unauthorized — не передан или устарел токен |
| 403 | Forbidden — недостаточно прав для действия |
| 404 | Not Found — ресурс не найден |
| 409 | Conflict — конфликт (дубликат и т.п.) |
| 422 | Unprocessable Entity — ошибка валидации (детали в errors[]) |
| 500 | Internal Server Error |


## 13.3 Валидация данных
Значения КПЭ: целое число от 0 до 100
Сумма весов КПЭ показателей для одного набора не должна превышать 1.0
Priority: допустимые значения — "high", "medium", "low"
Email: должен заканчиваться на @oshsu.kg (проверка на домен)
Дедлайны: дата не может быть в прошлом при создании задачи
Загружаемые файлы: максимальный размер 50 МБ, разрешённые форматы — PDF, DOCX, JPG, PNG

## 13.4 Нефункциональные требования
Время ответа API <= 1 секунды для 95% запросов
Поддержка CORS для домена фронтенда
Rate limiting: не более 100 запросов в минуту на IP
Хранение истории расчётов КПЭ за все периоды
Soft delete для всех сущностей (поле deleted_at)
Логирование всех изменений данных (audit log)
Соответствие требованиям защиты персональных данных КР
Документация API в формате Swagger/OpenAPI 3.0 по адресу /api/docs

# 16. CORS и переменные окружения
## 14.1 Переменная окружения
Фронтенд использует переменную VITE_API_BACKEND_URL из файла .env. Back-end должен быть доступен по этому URL.

## 14.2 Необходимые CORS-заголовки
Access-Control-Allow-Origin: <frontend_domain>
Access-Control-Allow-Methods: GET, POST, PUT, PATCH, DELETE, OPTIONS
Access-Control-Allow-Headers: Content-Type, Authorization

# 17. Очерёдность реализации (приоритеты)
## Фаза 1 — Критичная (Sprint 1-2):
Аутентификация (POST /auth/login, POST /auth/refresh, GET /auth/me)
Структура: Факультеты, Кафедры, Пользователи (CRUD + роли)
Задачи: CRUD, статусы, маршрутизация
КПЭ: показатели, значения, расчёт + запись KPI_Result при каждом POST /kpi/value

## Фаза 2 — Важная (Sprint 3-4):
Публикации: CRUD, клиент передаёт путь к файлу как строку
Документы/УМК: приём пути файла, цепочка согласования
Согласования (Approvals): approve/reject для проректора
Аналитика ректора и проректора (все GET возвращают [] / 0 при пустых данных)

## Фаза 3 — Дополнительная (Sprint 5+):
Планёрка (Planerka Calendar)
Нагрузка кафедр (Department Load)
Аналитика декана
Стратегические цели, Гранты, Программы
Экспорт отчётов (согласовать контракт с фронтендом)
Уведомления (алерты, дедлайны)

# 18. Контакты и обратная связь
По всем вопросам, связанным с данным ТЗ, обращаться к Front-End разработчику.
Документ составлен на основе анализа исходного кода проекта kpi_oshsu (React + TypeScript).
При расхождении требований ТЗ с реальным поведением фронтенда — руководствоваться кодом фронтенда.

Конец документа