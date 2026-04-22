from unittest.mock import MagicMock

from django.test import TestCase

from apps.common.permissions import make_role_permission


class MakeRolePermissionTests(TestCase):
    def _request(self, *, authenticated=True, role=None):
        user = MagicMock()
        user.is_authenticated = authenticated
        user.role = role
        request = MagicMock()
        request.user = user
        return request

    def test_authenticated_user_with_matching_role_allowed(self):
        Perm = make_role_permission(0, 1)
        self.assertTrue(Perm().has_permission(self._request(role=1), None))

    def test_authenticated_user_with_other_role_denied(self):
        Perm = make_role_permission(0, 1)
        self.assertFalse(Perm().has_permission(self._request(role=7), None))

    def test_unauthenticated_user_denied_even_with_matching_role(self):
        Perm = make_role_permission(0)
        self.assertFalse(
            Perm().has_permission(self._request(authenticated=False, role=0), None)
        )

    def test_factory_returns_distinct_classes(self):
        A = make_role_permission(0)
        B = make_role_permission(1)
        self.assertIsNot(A, B)

    def test_single_role_works(self):
        Perm = make_role_permission(5)
        self.assertTrue(Perm().has_permission(self._request(role=5), None))
        self.assertFalse(Perm().has_permission(self._request(role=6), None))
