from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from apps.users.models import Role, User


class LoginViewTests(APITestCase):
    def setUp(self):
        self.url = reverse("auth-login")
        self.user = User.objects.create_user(
            email="teacher@oshsu.kg", password="pass12345", full_name="Test Teacher"
        )

    def test_valid_login_returns_acces_and_refresh(self):
        res = self.client.post(
            self.url,
            {"login": "teacher@oshsu.kg", "password": "pass12345"},
            format="json",
        )
        self.assertEqual(res.status_code, 200)
        self.assertIn("acces", res.data)
        self.assertNotIn("access", res.data)
        self.assertIn("refresh", res.data)
        self.assertTrue(res.data["acces"])
        self.assertTrue(res.data["refresh"])

    def test_invalid_password_returns_401(self):
        res = self.client.post(
            self.url,
            {"login": "teacher@oshsu.kg", "password": "wrong"},
            format="json",
        )
        self.assertEqual(res.status_code, 401)

    def test_nonexistent_user_returns_401(self):
        res = self.client.post(
            self.url,
            {"login": "nope@oshsu.kg", "password": "x"},
            format="json",
        )
        self.assertEqual(res.status_code, 401)

    def test_inactive_user_returns_401(self):
        self.user.is_active = False
        self.user.save()
        res = self.client.post(
            self.url,
            {"login": "teacher@oshsu.kg", "password": "pass12345"},
            format="json",
        )
        self.assertEqual(res.status_code, 401)

    def test_missing_fields_returns_422(self):
        res = self.client.post(self.url, {}, format="json")
        self.assertEqual(res.status_code, 422)
        self.assertIn("error", res.data)

    def test_login_case_insensitive(self):
        res = self.client.post(
            self.url,
            {"login": "Teacher@OSHSU.KG", "password": "pass12345"},
            format="json",
        )
        self.assertEqual(res.status_code, 200)


class RefreshViewTests(APITestCase):
    def setUp(self):
        self.url = reverse("auth-refresh")
        self.user = User.objects.create_user(
            email="t@oshsu.kg", password="pass12345"
        )
        self.refresh = str(RefreshToken.for_user(self.user))

    def test_valid_refresh_returns_new_pair_with_acces_key(self):
        res = self.client.post(self.url, {"token": self.refresh}, format="json")
        self.assertEqual(res.status_code, 200)
        self.assertIn("acces", res.data)
        self.assertNotIn("access", res.data)
        self.assertIn("refresh", res.data)

    def test_invalid_token_returns_401(self):
        res = self.client.post(self.url, {"token": "not.a.jwt"}, format="json")
        self.assertEqual(res.status_code, 401)

    def test_reused_refresh_after_rotation_returns_401(self):
        self.client.post(self.url, {"token": self.refresh}, format="json")
        res = self.client.post(self.url, {"token": self.refresh}, format="json")
        self.assertEqual(res.status_code, 401)

    def test_missing_token_returns_422(self):
        res = self.client.post(self.url, {}, format="json")
        self.assertEqual(res.status_code, 422)


class LogoutViewTests(APITestCase):
    def setUp(self):
        self.url = reverse("auth-logout")
        self.refresh_url = reverse("auth-refresh")
        self.user = User.objects.create_user(
            email="t@oshsu.kg", password="pass12345"
        )
        self.refresh = RefreshToken.for_user(self.user)
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {self.refresh.access_token}"
        )

    def test_unauthenticated_returns_401(self):
        self.client.credentials()
        res = self.client.post(self.url, {"refresh": str(self.refresh)}, format="json")
        self.assertEqual(res.status_code, 401)

    def test_valid_logout_returns_204(self):
        res = self.client.post(self.url, {"refresh": str(self.refresh)}, format="json")
        self.assertEqual(res.status_code, 204)

    def test_logout_blacklists_refresh_token(self):
        self.client.post(self.url, {"refresh": str(self.refresh)}, format="json")
        self.client.credentials()
        res = self.client.post(
            self.refresh_url, {"token": str(self.refresh)}, format="json"
        )
        self.assertEqual(res.status_code, 401)

    def test_invalid_refresh_returns_401(self):
        res = self.client.post(self.url, {"refresh": "not.a.jwt"}, format="json")
        self.assertEqual(res.status_code, 401)


class MeViewTests(APITestCase):
    def setUp(self):
        self.url = reverse("auth-me")
        self.user = User.objects.create_user(
            email="t@oshsu.kg",
            password="pass12345",
            full_name="Жооке Алиев",
            role=Role.DEAN,
        )

    def test_unauthenticated_returns_401(self):
        res = self.client.get(self.url)
        self.assertEqual(res.status_code, 401)

    def test_authenticated_returns_profile(self):
        access = RefreshToken.for_user(self.user).access_token
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
        res = self.client.get(self.url)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data["email"], "t@oshsu.kg")
        self.assertEqual(res.data["full_name"], "Жооке Алиев")
        self.assertEqual(res.data["role"], Role.DEAN.value)
        self.assertTrue(res.data["is_active"])
        self.assertIn("id", res.data)
