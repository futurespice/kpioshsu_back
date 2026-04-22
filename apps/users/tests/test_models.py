import uuid

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase

from apps.users.models import Role, User


class RoleTests(TestCase):
    def test_role_values_match_spec(self):
        self.assertEqual(Role.ADMIN.value, 0)
        self.assertEqual(Role.RECTOR.value, 1)
        self.assertEqual(Role.VICE_RECTOR.value, 2)
        self.assertEqual(Role.SCIENCE_DEP.value, 3)
        self.assertEqual(Role.STUDENT_AFFAIRS.value, 4)
        self.assertEqual(Role.DEAN.value, 5)
        self.assertEqual(Role.HEAD_OF_DEPT.value, 6)
        self.assertEqual(Role.TEACHER.value, 7)


class UserManagerTests(TestCase):
    def test_create_user_success(self):
        user = User.objects.create_user(
            email="teacher@oshsu.kg", password="pass12345"
        )
        self.assertEqual(user.email, "teacher@oshsu.kg")
        self.assertTrue(user.check_password("pass12345"))
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertEqual(user.role, Role.TEACHER)

    def test_create_user_normalizes_email_case(self):
        user = User.objects.create_user(
            email="Teacher@OshSu.Kg", password="pass12345"
        )
        self.assertEqual(user.email, "teacher@oshsu.kg")

    def test_create_user_rejects_non_oshsu_email(self):
        with self.assertRaises(ValidationError):
            User.objects.create_user(email="user@gmail.com", password="x")

    def test_create_user_empty_email_raises(self):
        with self.assertRaises(ValueError):
            User.objects.create_user(email="", password="x")

    def test_create_superuser_sets_admin_role_and_flags(self):
        user = User.objects.create_superuser(
            email="admin@oshsu.kg", password="pass12345"
        )
        self.assertEqual(user.role, Role.ADMIN)
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)


class UserModelTests(TestCase):
    def test_uuid_primary_key(self):
        user = User.objects.create_user(email="a@oshsu.kg", password="pass12345")
        self.assertIsInstance(user.id, uuid.UUID)

    def test_password_is_hashed(self):
        user = User.objects.create_user(email="a@oshsu.kg", password="plain")
        self.assertNotEqual(user.password, "plain")
        self.assertTrue(user.check_password("plain"))

    def test_email_must_be_unique(self):
        User.objects.create_user(email="x@oshsu.kg", password="pass12345")
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                User.objects.create_user(email="x@oshsu.kg", password="pass12345")

    def test_default_role_is_teacher(self):
        user = User.objects.create_user(email="t@oshsu.kg", password="pass12345")
        self.assertEqual(user.role, Role.TEACHER)

    def test_explicit_role_respected(self):
        user = User.objects.create_user(
            email="d@oshsu.kg", password="pass12345", role=Role.DEAN
        )
        self.assertEqual(user.role, Role.DEAN)

    def test_soft_delete_hides_from_default_manager(self):
        user = User.objects.create_user(email="a@oshsu.kg", password="pass12345")
        user.soft_delete()
        self.assertFalse(User.objects.filter(pk=user.pk).exists())
        self.assertTrue(User.all_objects.filter(pk=user.pk).exists())

    def test_str_returns_email(self):
        user = User.objects.create_user(email="a@oshsu.kg", password="pass12345")
        self.assertEqual(str(user), "a@oshsu.kg")

    def test_username_field_is_email(self):
        self.assertEqual(User.USERNAME_FIELD, "email")

    def test_full_name_accepted_on_create(self):
        user = User.objects.create_user(
            email="f@oshsu.kg", password="pass12345", full_name="Иван Иванов"
        )
        self.assertEqual(user.full_name, "Иван Иванов")
