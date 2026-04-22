from django.test import TestCase
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError

from apps.common.exceptions import custom_exception_handler


class CustomExceptionHandlerTests(TestCase):
    def test_returns_none_for_non_drf_exception(self):
        self.assertIsNone(custom_exception_handler(ValueError("boom"), {}))

    def test_formats_validation_error(self):
        exc = ValidationError({"field": ["required"]})
        response = custom_exception_handler(exc, {})
        self.assertIsNotNone(response)
        self.assertIn("error", response.data)
        self.assertIn("code", response.data)
        self.assertIn("details", response.data)
        self.assertEqual(response.data["code"], "VALIDATIONERROR")

    def test_validation_error_status_is_422(self):
        response = custom_exception_handler(ValidationError("bad"), {})
        self.assertEqual(response.status_code, 422)

    def test_formats_not_found(self):
        response = custom_exception_handler(NotFound(), {})
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data["code"], "NOTFOUND")

    def test_formats_permission_denied(self):
        response = custom_exception_handler(PermissionDenied(), {})
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.data["code"], "PERMISSIONDENIED")
