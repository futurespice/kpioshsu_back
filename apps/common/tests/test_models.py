import uuid

from django.db import connection, models
from django.test import TestCase

from apps.common.models import BaseModel


class ConcreteForTests(BaseModel):
    name = models.CharField(max_length=100)

    class Meta:
        app_label = "common"
        managed = False


class BaseModelTests(TestCase):
    @classmethod
    def setUpClass(cls):
        with connection.schema_editor() as editor:
            editor.create_model(ConcreteForTests)
        super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        with connection.schema_editor() as editor:
            editor.delete_model(ConcreteForTests)

    def test_uuid_primary_key_auto_generated(self):
        obj = ConcreteForTests.objects.create(name="x")
        self.assertIsInstance(obj.id, uuid.UUID)

    def test_timestamps_populated_on_create(self):
        obj = ConcreteForTests.objects.create(name="x")
        self.assertIsNotNone(obj.created_at)
        self.assertIsNotNone(obj.updated_at)
        self.assertIsNone(obj.deleted_at)

    def test_soft_delete_sets_deleted_at(self):
        obj = ConcreteForTests.objects.create(name="x")
        obj.soft_delete()
        self.assertIsNotNone(obj.deleted_at)

    def test_default_manager_excludes_soft_deleted(self):
        obj = ConcreteForTests.objects.create(name="x")
        obj.soft_delete()
        self.assertFalse(ConcreteForTests.objects.filter(id=obj.id).exists())

    def test_all_objects_includes_soft_deleted(self):
        obj = ConcreteForTests.objects.create(name="x")
        obj.soft_delete()
        self.assertTrue(ConcreteForTests.all_objects.filter(id=obj.id).exists())

    def test_soft_delete_does_not_hard_delete(self):
        obj = ConcreteForTests.objects.create(name="x")
        pk = obj.id
        obj.soft_delete()
        self.assertTrue(ConcreteForTests.all_objects.filter(id=pk).exists())
