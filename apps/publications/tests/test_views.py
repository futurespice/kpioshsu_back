from datetime import date

from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from apps.publications.models import JournalType, Publication
from apps.users.models import Role, User


class _AuthMixin:
    def _auth(self, user):
        token = RefreshToken.for_user(user).access_token
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")


class _BasePubTestCase(_AuthMixin, APITestCase):
    url = "/api/publications/"

    def setUp(self):
        self.admin = User.objects.create_user(
            email="admin@oshsu.kg", password="p", role=Role.ADMIN
        )
        self.teacher = User.objects.create_user(
            email="t@oshsu.kg", password="p", role=Role.TEACHER
        )
        self.other_teacher = User.objects.create_user(
            email="t2@oshsu.kg", password="p", role=Role.TEACHER
        )
        self.dean = User.objects.create_user(
            email="dean@oshsu.kg", password="p", role=Role.DEAN
        )
        self.valid_payload = {
            "title": "Методы анализа данных",
            "journal": "Nature",
            "journal_type": JournalType.SCOPUS,
            "pub_date": "2025-10-01",
            "is_archived": False,
            "academic_year": "2025-2026",
        }


class PublicationCreateTests(_BasePubTestCase):
    def test_unauthenticated_returns_401(self):
        res = self.client.post(self.url, self.valid_payload, format="json")
        self.assertEqual(res.status_code, 401)

    def test_dean_cannot_create(self):
        self._auth(self.dean)
        res = self.client.post(self.url, self.valid_payload, format="json")
        self.assertEqual(res.status_code, 403)

    def test_teacher_can_create(self):
        self._auth(self.teacher)
        res = self.client.post(self.url, self.valid_payload, format="json")
        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.data["user"], self.teacher.id)
        self.assertEqual(res.data["kpi_points"], 25)

    def test_invalid_journal_type_returns_422(self):
        self._auth(self.teacher)
        bad = {**self.valid_payload, "journal_type": "unknown"}
        res = self.client.post(self.url, bad, format="json")
        self.assertEqual(res.status_code, 422)


class PublicationListFilterTests(_BasePubTestCase):
    def setUp(self):
        super().setUp()
        self.p1 = Publication.objects.create(
            user=self.teacher,
            title="A",
            journal_type=JournalType.SCOPUS,
            pub_date=date(2025, 10, 1),
            academic_year="2025-2026",
            is_archived=False,
        )
        self.p2 = Publication.objects.create(
            user=self.other_teacher,
            title="B",
            journal_type=JournalType.VAK,
            pub_date=date(2024, 10, 1),
            academic_year="2024-2025",
            is_archived=True,
        )

    def test_list_all(self):
        self._auth(self.admin)
        res = self.client.get(self.url)
        self.assertEqual(res.data["count"], 2)

    def test_filter_by_user_id(self):
        self._auth(self.admin)
        res = self.client.get(self.url, {"user_id": str(self.teacher.id)})
        self.assertEqual(res.data["count"], 1)
        self.assertEqual(res.data["result"][0]["id"], str(self.p1.id))

    def test_filter_by_year(self):
        self._auth(self.admin)
        res = self.client.get(self.url, {"year": "2024-2025"})
        self.assertEqual(res.data["count"], 1)

    def test_filter_by_type(self):
        self._auth(self.admin)
        res = self.client.get(self.url, {"type": "vak"})
        self.assertEqual(res.data["count"], 1)

    def test_filter_by_archived(self):
        self._auth(self.admin)
        res = self.client.get(self.url, {"archived": "true"})
        self.assertEqual(res.data["count"], 1)
        res2 = self.client.get(self.url, {"archived": "false"})
        self.assertEqual(res2.data["count"], 1)


class PublicationMyTests(_BasePubTestCase):
    def setUp(self):
        super().setUp()
        Publication.objects.create(
            user=self.teacher, title="A",
            journal_type=JournalType.SCOPUS, pub_date=date(2025, 10, 1),
            academic_year="2025-2026",
        )
        Publication.objects.create(
            user=self.teacher, title="B",
            journal_type=JournalType.VAK, pub_date=date(2024, 11, 1),
            academic_year="2024-2025",
        )
        Publication.objects.create(
            user=self.other_teacher, title="C",
            journal_type=JournalType.RINC, pub_date=date(2025, 3, 1),
            academic_year="2025-2026",
        )

    def test_my_returns_only_mine_grouped_by_year(self):
        self._auth(self.teacher)
        res = self.client.get(f"{self.url}my/")
        self.assertEqual(res.status_code, 200)
        self.assertIn("2025-2026", res.data)
        self.assertIn("2024-2025", res.data)
        self.assertEqual(len(res.data["2025-2026"]), 1)
        self.assertEqual(len(res.data["2024-2025"]), 1)


class PublicationUpdateDeleteTests(_BasePubTestCase):
    def setUp(self):
        super().setUp()
        self.pub = Publication.objects.create(
            user=self.teacher, title="A",
            journal_type=JournalType.SCOPUS, pub_date=date(2025, 10, 1),
            academic_year="2025-2026",
        )
        self.detail_url = f"{self.url}{self.pub.id}/"

    def test_non_owner_cannot_update(self):
        self._auth(self.other_teacher)
        res = self.client.patch(self.detail_url, {"title": "X"}, format="json")
        self.assertEqual(res.status_code, 403)

    def test_owner_can_update(self):
        self._auth(self.teacher)
        res = self.client.patch(self.detail_url, {"title": "X"}, format="json")
        self.assertEqual(res.status_code, 200)

    def test_admin_can_update(self):
        self._auth(self.admin)
        res = self.client.patch(self.detail_url, {"title": "adm"}, format="json")
        self.assertEqual(res.status_code, 200)

    def test_owner_delete_is_soft(self):
        self._auth(self.teacher)
        res = self.client.delete(self.detail_url)
        self.assertEqual(res.status_code, 204)
        self.assertTrue(Publication.all_objects.filter(id=self.pub.id).exists())
        self.assertFalse(Publication.objects.filter(id=self.pub.id).exists())


class PublicationStatsTests(_BasePubTestCase):
    def setUp(self):
        super().setUp()
        for jt in [JournalType.SCOPUS, JournalType.SCOPUS, JournalType.VAK, JournalType.RINC]:
            Publication.objects.create(
                user=self.teacher, title=f"T-{jt}",
                journal_type=jt, pub_date=date(2025, 1, 1),
                academic_year="2025-2026",
            )

    def test_unauthenticated_returns_401(self):
        res = self.client.get(f"{self.url}stats/{self.teacher.id}/")
        self.assertEqual(res.status_code, 401)

    def test_stats_shape(self):
        self._auth(self.dean)
        res = self.client.get(f"{self.url}stats/{self.teacher.id}/")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data["total_count"], 4)
        # 25 + 25 + 15 + 8 = 73
        self.assertEqual(res.data["total_points"], 73)
        self.assertEqual(res.data["by_type"]["scopus"], 2)
        self.assertEqual(res.data["by_type"]["vak"], 1)
        self.assertEqual(res.data["by_type"]["rinc"], 1)
