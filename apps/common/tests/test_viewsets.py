from unittest.mock import MagicMock

from django.test import TestCase

from apps.common.viewsets import BaseViewSet


class BaseViewSetDestroyTests(TestCase):
    def test_destroy_calls_soft_delete_and_returns_204(self):
        viewset = BaseViewSet()
        mock_instance = MagicMock()
        viewset.get_object = lambda: mock_instance

        response = viewset.destroy(request=MagicMock())

        mock_instance.soft_delete.assert_called_once_with()
        mock_instance.delete.assert_not_called()
        self.assertEqual(response.status_code, 204)
