"""Seed mock-данных для разработки и демо.

Запуск:
    python manage.py seed              # идемпотентно (не удаляет существующие)
    python manage.py seed --reset      # сначала чистит все таблицы (кроме admin)

Все пароли пользователей: ``Password123!``.
Логин администратора: ``admin@oshsu.kg``.
"""

import random
from datetime import date, timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.approvals.models import Approval, ApprovalStatus, ApprovalType
from apps.department_load.models import DeptLoad
from apps.departments.models import Department
from apps.documents.models import Document, DocType, DocumentStatus
from apps.faculties.models import Faculty
from apps.kpi.models import KPI, KPICategory, KPIValue, PeriodType
from apps.kpi.services import upsert_kpi_result
from apps.notifications.models import Notification, NotificationType
from apps.planerka.models import Planerka, PlanerkaPriority
from apps.publications.models import JournalType, Publication
from apps.strategic.models import (
    Grant,
    GrantStatus,
    Program,
    ProgramStatus,
    StrategicGoal,
)
from apps.tasks.models import Priority, Task, TaskStatus
from apps.users.models import Role, User


DEFAULT_PASSWORD = "Password123!"
ACADEMIC_YEAR = "2025-2026"


FACULTIES = [
    {"name": "Инженерный факультет", "short_name": "eng"},
    {"name": "Экономический факультет", "short_name": "eco"},
    {"name": "Гуманитарный факультет", "short_name": "hum"},
    {"name": "Естественнонаучный факультет", "short_name": "sci"},
]

DEPARTMENTS = [
    ("Кафедра информатики", "ИТ", "Инженерный факультет", 1200),
    ("Кафедра прикладной математики", "МАТ", "Инженерный факультет", 1100),
    ("Кафедра экономики", "ЭКО", "Экономический факультет", 1000),
    ("Кафедра истории", "ИСТ", "Гуманитарный факультет", 900),
    ("Кафедра философии", "ФИЛ", "Гуманитарный факультет", 850),
    ("Кафедра физики", "ФИЗ", "Естественнонаучный факультет", 1050),
]

KPI_DEFS = [
    ("Публикационная активность", KPICategory.SCIENCE, Decimal("0.20")),
    ("Качество преподавания", KPICategory.TEACHING, Decimal("0.20")),
    ("Методическое обеспечение", KPICategory.METHODOLOGY, Decimal("0.15")),
    ("Воспитательная работа", KPICategory.EDUCATION, Decimal("0.10")),
    ("Выполнение нагрузки", KPICategory.LOAD, Decimal("0.20")),
    ("Прочие достижения", KPICategory.OTHER, Decimal("0.15")),
]

TEACHER_FIRST = [
    "Айбек", "Бакыт", "Чолпон", "Динара", "Эрнис", "Гульнара", "Жамиля",
    "Канат", "Ляззат", "Мээрим", "Нурбек", "Омурбек", "Перизат", "Рахат",
    "Салтанат", "Талант", "Уран", "Ферюза", "Чынара", "Шайыр",
]
TEACHER_LAST = [
    "Абдыкадыров", "Бекмуратов", "Чыныбаев", "Джумалиев", "Эсенов",
    "Кенжебаев", "Маматов", "Нурланов", "Орозбеков", "Райымбеков",
]


def _email(prefix: str, idx: int | None = None) -> str:
    base = prefix if idx is None else f"{prefix}{idx}"
    return f"{base}@oshsu.kg"


def _create_user(email: str, *, role: int, full_name: str, faculty=None, department=None) -> User:
    user, created = User.objects.get_or_create(
        email=email,
        defaults={
            "full_name": full_name,
            "role": role,
            "faculty": faculty,
            "department": department,
            "is_active": True,
        },
    )
    if created:
        user.set_password(DEFAULT_PASSWORD)
        user.save(update_fields=["password"])
    else:
        changed = False
        if user.role != role:
            user.role = role
            changed = True
        if user.full_name != full_name:
            user.full_name = full_name
            changed = True
        if faculty is not None and user.faculty_id != faculty.id:
            user.faculty = faculty
            changed = True
        if department is not None and user.department_id != department.id:
            user.department = department
            changed = True
        if changed:
            user.save()
    return user


def _current_periods() -> dict[str, str]:
    today = date.today()
    return {
        PeriodType.MONTH: today.strftime("%Y-%m"),
        PeriodType.SEMESTER: f"{today.year}-{1 if today.month <= 6 else 2}",
        PeriodType.YEAR: ACADEMIC_YEAR,
    }


class Command(BaseCommand):
    help = "Заполнить БД mock-данными для разработки/демо."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Удалить существующие данные перед заполнением.",
        )
        parser.add_argument(
            "--seed", type=int, default=42, help="Зерно random (default: 42)."
        )

    @transaction.atomic
    def handle(self, *args, **opts):
        random.seed(opts["seed"])
        if opts["reset"]:
            self._reset()

        admin = self._create_admin()
        faculties = self._create_faculties()
        deans = self._create_deans(faculties)
        departments = self._create_departments(faculties)
        heads = self._create_heads(departments)
        teachers = self._create_teachers(departments)
        rector, vice_rector = self._create_top_management()
        science, students_aff = self._create_aux_management()

        kpis = self._create_kpis(admin)
        self._create_kpi_values(teachers, kpis)
        self._create_tasks(rector, vice_rector, deans, heads, teachers, faculties, departments)
        self._create_publications(teachers, kpis)
        documents = self._create_documents(teachers, departments)
        self._create_approvals(teachers, departments, documents, vice_rector)
        self._create_planerka(vice_rector, faculties)
        self._create_dept_loads(departments)
        self._create_strategic(faculties)
        self._create_notifications(rector, vice_rector, deans + heads + teachers)

        total_users = 1 + 2 + 2 + len(deans) + len(heads) + len(teachers)
        self.stdout.write(self.style.SUCCESS(f"Seed завершён. Всего пользователей: {total_users}"))
        self.stdout.write("─" * 50)
        self.stdout.write(f"Пароль для всех: {DEFAULT_PASSWORD}")
        self.stdout.write("─" * 50)
        self.stdout.write(f"Админ:        admin@oshsu.kg              (is_staff, is_superuser)")
        self.stdout.write(f"Ректор:       rector@oshsu.kg")
        self.stdout.write(f"Проректор:    vice@oshsu.kg")
        self.stdout.write(f"НИО:          science@oshsu.kg")
        self.stdout.write(f"Студ.отдел:   students@oshsu.kg")
        self.stdout.write(f"Деканы:       dean1..dean{len(deans)}@oshsu.kg            ({len(deans)})")
        self.stdout.write(f"Завкафедрой:  head1..head{len(heads)}@oshsu.kg            ({len(heads)})")
        self.stdout.write(f"Преподы:      teacher1..teacher{len(teachers)}@oshsu.kg     ({len(teachers)})")

    # ---------- reset ----------

    def _reset(self):
        self.stdout.write("Очистка таблиц...")
        Notification.objects.all().delete()
        Approval.objects.all().delete()
        Document.objects.all().delete()
        Publication.objects.all().delete()
        Task.objects.all().delete()
        Planerka.objects.all().delete()
        DeptLoad.objects.all().delete()
        from apps.kpi.models import KPIResult

        KPIResult.objects.all().delete()
        KPIValue.objects.all().delete()
        KPI.objects.all().delete()
        StrategicGoal.objects.all().delete()
        Grant.objects.all().delete()
        Program.objects.all().delete()
        User.objects.exclude(email="admin@oshsu.kg").delete()
        Department.objects.all().delete()
        Faculty.objects.all().delete()

    # ---------- users ----------

    def _create_admin(self) -> User:
        email = _email("admin")
        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                "full_name": "Системный администратор",
                "role": Role.ADMIN,
                "is_active": True,
                "is_staff": True,
                "is_superuser": True,
            },
        )
        if created:
            user.set_password(DEFAULT_PASSWORD)
            user.save(update_fields=["password"])
        else:
            update_fields = []
            if not user.is_staff:
                user.is_staff = True
                update_fields.append("is_staff")
            if not user.is_superuser:
                user.is_superuser = True
                update_fields.append("is_superuser")
            if user.role != Role.ADMIN:
                user.role = Role.ADMIN
                update_fields.append("role")
            if update_fields:
                user.save(update_fields=update_fields)
        return user

    def _create_top_management(self) -> tuple[User, User]:
        rector = _create_user(_email("rector"), role=Role.RECTOR, full_name="Ректор Университета")
        vice = _create_user(_email("vice"), role=Role.VICE_RECTOR, full_name="Проректор по учебной работе")
        return rector, vice

    def _create_aux_management(self) -> tuple[User, User]:
        science = _create_user(_email("science"), role=Role.SCIENCE_DEP, full_name="Начальник НИО")
        students = _create_user(_email("students"), role=Role.STUDENT_AFFAIRS, full_name="Начальник студенческого отдела")
        return science, students

    def _create_faculties(self) -> dict[str, Faculty]:
        result = {}
        for f in FACULTIES:
            obj, _ = Faculty.objects.get_or_create(
                name=f["name"], defaults={"short_name": f["short_name"], "is_active": True}
            )
            result[f["name"]] = obj
        return result

    def _create_deans(self, faculties: dict[str, Faculty]) -> list[User]:
        deans = []
        for idx, (name, fac) in enumerate(faculties.items(), start=1):
            dean = _create_user(
                _email("dean", idx),
                role=Role.DEAN,
                full_name=f"Декан {fac.short_name.upper()}",
                faculty=fac,
            )
            if fac.dean_id != dean.id:
                fac.dean = dean
                fac.save(update_fields=["dean"])
            deans.append(dean)
        return deans

    def _create_departments(self, faculties: dict[str, Faculty]) -> list[Department]:
        result = []
        for name, short, fac_name, target in DEPARTMENTS:
            obj, _ = Department.objects.get_or_create(
                name=name,
                defaults={
                    "short": short,
                    "faculty": faculties[fac_name],
                    "target_hours": target,
                },
            )
            result.append(obj)
        return result

    def _create_heads(self, departments: list[Department]) -> list[User]:
        heads = []
        for idx, dept in enumerate(departments, start=1):
            head = _create_user(
                _email("head", idx),
                role=Role.HEAD_OF_DEPT,
                full_name=f"Завкафедрой {dept.short}",
                faculty=dept.faculty,
                department=dept,
            )
            if dept.head_id != head.id:
                dept.head = head
                dept.save(update_fields=["head"])
            heads.append(head)
        return heads

    def _create_teachers(self, departments: list[Department]) -> list[User]:
        teachers = []
        idx = 0
        for dept in departments:
            for _ in range(2):
                idx += 1
                first = random.choice(TEACHER_FIRST)
                last = random.choice(TEACHER_LAST)
                teacher = _create_user(
                    _email("teacher", idx),
                    role=Role.TEACHER,
                    full_name=f"{last} {first}",
                    faculty=dept.faculty,
                    department=dept,
                )
                teachers.append(teacher)
        return teachers

    # ---------- kpi ----------

    def _create_kpis(self, admin: User) -> list[KPI]:
        result = []
        for name, category, weight in KPI_DEFS:
            obj, _ = KPI.objects.get_or_create(
                name=name,
                defaults={
                    "description": f"Показатель: {name}",
                    "weight": weight,
                    "category": category,
                    "is_active": True,
                    "created_by": admin,
                },
            )
            result.append(obj)
        return result

    def _create_kpi_values(self, teachers: list[User], kpis: list[KPI]):
        periods = _current_periods()
        # Текущий месяц + прошлый месяц + семестр + год
        today = date.today()
        prev = (today.replace(day=1) - timedelta(days=1))
        period_pairs = [
            (PeriodType.MONTH, periods[PeriodType.MONTH]),
            (PeriodType.MONTH, prev.strftime("%Y-%m")),
            (PeriodType.SEMESTER, periods[PeriodType.SEMESTER]),
            (PeriodType.YEAR, periods[PeriodType.YEAR]),
        ]

        touched = set()
        for teacher in teachers:
            for ptype, pvalue in period_pairs:
                for kpi in kpis:
                    KPIValue.objects.update_or_create(
                        user=teacher,
                        kpi=kpi,
                        period_type=ptype,
                        period_value=pvalue,
                        defaults={"value": Decimal(random.randint(50, 100))},
                    )
                touched.add((teacher.id, ptype, pvalue))

        for user_id, ptype, pvalue in touched:
            upsert_kpi_result(user_id, ptype, pvalue)

    # ---------- tasks ----------

    def _create_tasks(
        self,
        rector: User,
        vice: User,
        deans: list[User],
        heads: list[User],
        teachers: list[User],
        faculties: dict[str, Faculty],
        departments: list[Department],
    ):
        priorities = list(Priority.values)
        statuses = [TaskStatus.PENDING, TaskStatus.IN_PROGRESS, TaskStatus.COMPLETED]
        today = date.today()
        plans = [
            (rector, vice, "Подготовить стратегический отчёт по факультету", None, None),
            (rector, vice, "Согласовать план НИР на 2026", None, None),
            (vice, random.choice(deans), "Отчёт о выполнении УМК", None, None),
            (vice, random.choice(deans), "Анализ публикационной активности", None, None),
        ]
        for from_u, to_u, title, dept, fac in plans:
            Task.objects.get_or_create(
                title=title,
                from_user=from_u,
                to_user=to_u,
                defaults={
                    "description": f"Автоматически созданная задача: {title}",
                    "priority": random.choice(priorities),
                    "status": random.choice(statuses),
                    "points": random.randint(5, 20),
                    "deadline": today + timedelta(days=random.randint(7, 60)),
                    "to_dept": dept,
                    "faculty": fac,
                    "hours": random.randint(8, 40),
                },
            )

        # Задачи от завкафедрой преподавателям
        for head in heads:
            dept_teachers = [t for t in teachers if t.department_id == head.department_id]
            for teacher in dept_teachers[:2]:
                Task.objects.get_or_create(
                    title=f"Подготовить методические материалы для {teacher.full_name}",
                    from_user=head,
                    to_user=teacher,
                    defaults={
                        "priority": random.choice(priorities),
                        "status": random.choice(statuses),
                        "points": random.randint(3, 10),
                        "deadline": today + timedelta(days=random.randint(3, 30)),
                        "to_dept": head.department,
                        "hours": random.randint(4, 20),
                    },
                )

        # Несколько просроченных задач — для UniversityAlertsView
        for i in range(3):
            t = random.choice(teachers)
            head = next((h for h in heads if h.department_id == t.department_id), heads[0])
            Task.objects.get_or_create(
                title=f"Просроченная задача #{i + 1}",
                from_user=head,
                to_user=t,
                defaults={
                    "priority": Priority.HIGH,
                    "status": TaskStatus.IN_PROGRESS,
                    "points": 5,
                    "deadline": today - timedelta(days=random.randint(1, 14)),
                    "to_dept": t.department,
                    "hours": 10,
                },
            )

    # ---------- publications ----------

    def _create_publications(self, teachers: list[User], kpis: list[KPI]):
        journal_types = list(JournalType.values)
        science_kpi = next((k for k in kpis if k.category == KPICategory.SCIENCE), None)
        today = date.today()
        for teacher in teachers:
            for i in range(random.randint(1, 3)):
                jtype = random.choice(journal_types)
                Publication.objects.get_or_create(
                    user=teacher,
                    title=f"Статья {i + 1} автора {teacher.full_name}",
                    defaults={
                        "journal": f"Журнал {jtype.upper()} {random.randint(1, 50)}",
                        "journal_type": jtype,
                        "pub_date": today - timedelta(days=random.randint(10, 365)),
                        "url": f"https://storage.oshsu.kg/pub/{teacher.id}_{i}.pdf",
                        "coauthors": "",
                        "kpi_indicator": science_kpi,
                        "evidence_file": f"https://storage.oshsu.kg/evidence/{teacher.id}_{i}.pdf",
                        "academic_year": ACADEMIC_YEAR,
                    },
                )

    # ---------- documents ----------

    def _create_documents(self, teachers: list[User], departments: list[Department]) -> list[Document]:
        doc_types = list(DocType.values)
        statuses = list(DocumentStatus.values)
        result = []
        for dept in departments:
            dept_teachers = [t for t in teachers if t.department_id == dept.id]
            if not dept_teachers:
                continue
            for i in range(random.randint(1, 3)):
                teacher = random.choice(dept_teachers)
                doc_type = random.choice(doc_types)
                status = random.choice(statuses)
                doc, _ = Document.objects.get_or_create(
                    title=f"{doc_type.upper()} {dept.short} #{i + 1}",
                    user=teacher,
                    department=dept,
                    defaults={
                        "doc_type": doc_type,
                        "file_path": f"https://storage.oshsu.kg/docs/{dept.short}_{i}.pdf",
                        "file_size": random.randint(50000, 5000000),
                        "mime_type": "application/pdf",
                        "status": status,
                        "approved_by_dept": status != DocumentStatus.PENDING,
                        "approved_by_dean": status == DocumentStatus.APPROVED,
                        "approved_by_rector": status == DocumentStatus.APPROVED,
                        "academic_year": ACADEMIC_YEAR,
                    },
                )
                if status == DocumentStatus.APPROVED and not doc.approved_at:
                    doc.approved_at = timezone.now()
                    doc.save(update_fields=["approved_at"])
                result.append(doc)

        # Зависшие документы — для UniversityAlertsView
        old = timezone.now() - timedelta(days=14)
        for i in range(2):
            teacher = random.choice(teachers)
            doc, created = Document.objects.get_or_create(
                title=f"Зависший документ #{i + 1}",
                user=teacher,
                department=teacher.department,
                defaults={
                    "doc_type": DocType.UMK,
                    "file_path": f"https://storage.oshsu.kg/docs/stuck_{i}.pdf",
                    "status": DocumentStatus.PENDING,
                    "academic_year": ACADEMIC_YEAR,
                },
            )
            if created:
                Document.objects.filter(pk=doc.pk).update(created_at=old)
            result.append(doc)
        return result

    # ---------- approvals ----------

    def _create_approvals(
        self,
        teachers: list[User],
        departments: list[Department],
        documents: list[Document],
        vice: User,
    ):
        types = list(ApprovalType.values)
        for i, doc in enumerate(documents[:10]):
            status = random.choice(list(ApprovalStatus.values))
            Approval.objects.get_or_create(
                title=f"Согласование: {doc.title}",
                from_user=doc.user,
                document=doc,
                defaults={
                    "type": random.choice(types),
                    "department": doc.department,
                    "status": status,
                    "resolved_at": timezone.now() if status != ApprovalStatus.PENDING else None,
                    "resolved_by": vice if status != ApprovalStatus.PENDING else None,
                    "rejection_reason": "Доработать раздел 3" if status == ApprovalStatus.REJECTED else "",
                },
            )

    # ---------- planerka ----------

    def _create_planerka(self, vice: User, faculties: dict[str, Faculty]):
        today = date.today()
        items = [
            ("Совещание по ректорскому отчёту", PlanerkaPriority.HIGH, 7, "scheduled"),
            ("Анализ КПЭ за месяц", PlanerkaPriority.MEDIUM, 14, "scheduled"),
            ("Обсуждение нагрузки кафедр", PlanerkaPriority.MEDIUM, 21, "scheduled"),
            ("Защита УМК", PlanerkaPriority.HIGH, 30, "scheduled"),
            ("Подведение итогов семестра", PlanerkaPriority.LOW, 45, "scheduled"),
        ]
        fac_names = list(faculties.keys())
        for title, priority, day_off, status in items:
            Planerka.objects.get_or_create(
                title=title,
                created_by=vice,
                defaults={
                    "description": f"Событие: {title}",
                    "faculty": random.choice(fac_names),
                    "priority": priority,
                    "deadline": today + timedelta(days=day_off),
                    "points": random.randint(5, 15),
                    "hours": random.randint(2, 6),
                    "status": status,
                },
            )

    # ---------- dept load ----------

    def _create_dept_loads(self, departments: list[Department]):
        for dept in departments:
            target = dept.target_hours or 1000
            for semester in (1, 2):
                DeptLoad.objects.update_or_create(
                    department=dept,
                    academic_year=ACADEMIC_YEAR,
                    semester=semester,
                    defaults={
                        "target_hours": target,
                        "actual_hours": int(target * random.uniform(0.6, 1.05)),
                    },
                )

    # ---------- strategic ----------

    def _create_strategic(self, faculties: dict[str, Faculty]):
        goals = [
            ("Рост публикаций в Scopus до 120 ед.", 89, 120, "ед."),
            ("Доля аккредитованных программ", 72, 100, "%"),
            ("Объём грантовой деятельности", 45, 80, "млн С"),
            ("Средний КПЭ преподавателей", 78, 90, "балл"),
            ("Доля защищённых УМК", 64, 95, "%"),
        ]
        for title, current, target, unit in goals:
            StrategicGoal.objects.get_or_create(
                title=title,
                academic_year=ACADEMIC_YEAR,
                defaults={
                    "current_value": Decimal(current),
                    "target_value": Decimal(target),
                    "unit": unit,
                    "is_active": True,
                },
            )

        fac_list = list(faculties.values())
        grants = [
            ("Грант на НИР по ИИ", Decimal("5000000"), GrantStatus.ACTIVE),
            ("Грант на развитие лаборатории", Decimal("3500000"), GrantStatus.ACTIVE),
            ("Грант на международное сотрудничество", Decimal("8000000"), GrantStatus.PENDING),
            ("Завершённый грант 2024", Decimal("2000000"), GrantStatus.COMPLETED),
            ("Грант на цифровизацию", Decimal("4500000"), GrantStatus.ACTIVE),
        ]
        for title, amount, status in grants:
            Grant.objects.get_or_create(
                title=title,
                year=2026,
                defaults={
                    "amount": amount,
                    "status": status,
                    "faculty": random.choice(fac_list),
                },
            )

        programs = [
            ("Информатика и вычислительная техника", ProgramStatus.ACCREDITED),
            ("Прикладная математика", ProgramStatus.ACCREDITED),
            ("Экономика", ProgramStatus.ACCREDITED),
            ("Менеджмент", ProgramStatus.PENDING),
            ("История", ProgramStatus.ACCREDITED),
            ("Философия", ProgramStatus.ACCREDITED),
            ("Физика", ProgramStatus.ACCREDITED),
            ("Биология", ProgramStatus.PENDING),
        ]
        for title, status in programs:
            Program.objects.get_or_create(
                title=title,
                defaults={
                    "faculty": random.choice(fac_list),
                    "status": status,
                    "accredited_at": date(2024, 6, 1) if status == ProgramStatus.ACCREDITED else None,
                    "expires_at": date(2029, 6, 1) if status == ProgramStatus.ACCREDITED else None,
                },
            )

    # ---------- notifications ----------

    def _create_notifications(self, rector: User, vice: User, others: list[User]):
        items = [
            (rector, NotificationType.ALERT, "Просроченные задачи", "У 3 задач истёк дедлайн."),
            (rector, NotificationType.ACHIEVEMENT, "Цель достигнута", "Программа аккредитована."),
            (vice, NotificationType.DEADLINE, "Согласование УМК", "На согласовании 5 документов."),
            (vice, NotificationType.INFO, "Планёрка завтра", "Совещание в 10:00."),
        ]
        for user, ntype, title, message in items:
            Notification.objects.get_or_create(
                user=user, title=title, defaults={"type": ntype, "message": message}
            )
        for user in random.sample(others, min(10, len(others))):
            Notification.objects.get_or_create(
                user=user,
                title="Новая задача",
                defaults={
                    "type": NotificationType.INFO,
                    "message": "Вам назначена новая задача.",
                },
            )
