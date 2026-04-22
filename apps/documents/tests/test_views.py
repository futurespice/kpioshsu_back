from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from apps.departments.models import Department
from apps.documents.models import Document, DocType, DocumentStatus
from apps.faculties.models import Faculty
from apps.users.models import Role, User


class _AuthMixin:
    def _auth(self, user):
        token = RefreshToken.for_user(user).access_token
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")


class _BaseDocTestCase(_AuthMixin, APITestCase):
    url = "/api/documents/"

    def setUp(self):
        self.admin = User.objects.create_user(
            email="admin@oshsu.kg", password="p", role=Role.ADMIN
        )
        self.teacher = User.objects.create_user(
            email="t@oshsu.kg", password="p", role=Role.TEACHER
        )
        self.head = User.objects.create_user(
            email="head@oshsu.kg", password="p", role=Role.HEAD_OF_DEPT
        )
        self.dean = User.objects.create_user(
            email="dean@oshsu.kg", password="p", role=Role.DEAN
        )
        self.vice = User.objects.create_user(
            email="vice@oshsu.kg", password="p", role=Role.VICE_RECTOR
        )
        self.rector = User.objects.create_user(
            email="rector@oshsu.kg", password="p", role=Role.RECTOR
        )
        self.faculty = Faculty.objects.create(name="Инж")
        self.dept = Department.objects.create(name="ИТ", faculty=self.faculty)
        self.payload = {
            "title": "УМК по базам данных",
            "doc_type": DocType.UMK,
            "department": str(self.dept.id),
            "file_path": "/uploads/umk.pdf",
            "file_size": 1024,
            "mime_type": "application/pdf",
            "academic_year": "2025-2026",
        }


class DocumentCreateTests(_BaseDocTestCase):
    def test_unauthenticated_returns_401(self):
        res = self.client.post(self.url, self.payload, format="json")
        self.assertEqual(res.status_code, 401)

    def test_dean_cannot_upload(self):
        self._auth(self.dean)
        res = self.client.post(self.url, self.payload, format="json")
        self.assertEqual(res.status_code, 403)

    def test_teacher_can_upload(self):
        self._auth(self.teacher)
        res = self.client.post(self.url, self.payload, format="json")
        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.data["user"], self.teacher.id)
        self.assertEqual(res.data["status"], DocumentStatus.PENDING)
        self.assertFalse(res.data["approved_by_dept"])

    def test_invalid_doc_type_returns_422(self):
        self._auth(self.teacher)
        bad = {**self.payload, "doc_type": "unknown"}
        res = self.client.post(self.url, bad, format="json")
        self.assertEqual(res.status_code, 422)


class DocumentListFilterTests(_BaseDocTestCase):
    def setUp(self):
        super().setUp()
        self.d1 = Document.objects.create(
            title="A", doc_type=DocType.UMK, user=self.teacher,
            department=self.dept, file_path="/a", academic_year="2025-2026",
            status=DocumentStatus.PENDING,
        )
        other_dept = Department.objects.create(name="МАТ", faculty=self.faculty)
        self.d2 = Document.objects.create(
            title="B", doc_type=DocType.SYLLABUS, user=self.head,
            department=other_dept, file_path="/b", academic_year="2024-2025",
            status=DocumentStatus.APPROVED,
        )

    def test_filter_by_dept_id(self):
        self._auth(self.dean)
        res = self.client.get(self.url, {"dept_id": str(self.dept.id)})
        self.assertEqual(res.data["count"], 1)

    def test_filter_by_type(self):
        self._auth(self.dean)
        res = self.client.get(self.url, {"type": "syllabus"})
        self.assertEqual(res.data["count"], 1)

    def test_filter_by_status(self):
        self._auth(self.dean)
        res = self.client.get(self.url, {"status": "pending"})
        self.assertEqual(res.data["count"], 1)

    def test_filter_by_year(self):
        self._auth(self.dean)
        res = self.client.get(self.url, {"year": "2024-2025"})
        self.assertEqual(res.data["count"], 1)


class DocumentApproveTests(_BaseDocTestCase):
    def setUp(self):
        super().setUp()
        self.doc = Document.objects.create(
            title="A", doc_type=DocType.UMK, user=self.teacher,
            department=self.dept, file_path="/a", academic_year="2025-2026",
        )
        self.approve_url = f"{self.url}{self.doc.id}/approve/"

    def test_teacher_cannot_approve(self):
        self._auth(self.teacher)
        res = self.client.patch(self.approve_url, {"level": "dept"}, format="json")
        self.assertEqual(res.status_code, 403)

    def test_dean_approve_dept_level(self):
        self._auth(self.dean)
        res = self.client.patch(self.approve_url, {"level": "dept"}, format="json")
        self.assertEqual(res.status_code, 200)
        self.doc.refresh_from_db()
        self.assertTrue(self.doc.approved_by_dept)
        self.assertFalse(self.doc.approved_by_dean)
        self.assertEqual(self.doc.status, DocumentStatus.PENDING)

    def test_full_chain_sets_approved(self):
        for user, level in [(self.dean, "dept"), (self.dean, "dean"), (self.rector, "rector")]:
            self._auth(user)
            res = self.client.patch(self.approve_url, {"level": level}, format="json")
            self.assertEqual(res.status_code, 200)
        self.doc.refresh_from_db()
        self.assertEqual(self.doc.status, DocumentStatus.APPROVED)
        self.assertIsNotNone(self.doc.approved_at)

    def test_invalid_level_returns_422(self):
        self._auth(self.dean)
        res = self.client.patch(self.approve_url, {"level": "admin"}, format="json")
        self.assertEqual(res.status_code, 422)


class DocumentRejectTests(_BaseDocTestCase):
    def setUp(self):
        super().setUp()
        self.doc = Document.objects.create(
            title="A", doc_type=DocType.UMK, user=self.teacher,
            department=self.dept, file_path="/a", academic_year="2025-2026",
        )
        self.reject_url = f"{self.url}{self.doc.id}/reject/"

    def test_teacher_cannot_reject(self):
        self._auth(self.teacher)
        res = self.client.patch(self.reject_url, {"reason": "x"}, format="json")
        self.assertEqual(res.status_code, 403)

    def test_dean_can_reject(self):
        self._auth(self.dean)
        res = self.client.patch(
            self.reject_url, {"reason": "Не соответствует стандарту"}, format="json"
        )
        self.assertEqual(res.status_code, 200)
        self.doc.refresh_from_db()
        self.assertEqual(self.doc.status, DocumentStatus.REJECTED)
        self.assertEqual(self.doc.rejection_reason, "Не соответствует стандарту")

    def test_reject_without_reason_returns_422(self):
        self._auth(self.dean)
        res = self.client.patch(self.reject_url, {}, format="json")
        self.assertEqual(res.status_code, 422)


class DocumentDeleteTests(_BaseDocTestCase):
    def setUp(self):
        super().setUp()
        self.doc = Document.objects.create(
            title="A", doc_type=DocType.UMK, user=self.teacher,
            department=self.dept, file_path="/a", academic_year="2025-2026",
        )
        self.detail_url = f"{self.url}{self.doc.id}/"

    def test_other_teacher_cannot_delete(self):
        other = User.objects.create_user(
            email="other@oshsu.kg", password="p", role=Role.TEACHER
        )
        self._auth(other)
        res = self.client.delete(self.detail_url)
        self.assertEqual(res.status_code, 403)

    def test_owner_delete_is_soft(self):
        self._auth(self.teacher)
        res = self.client.delete(self.detail_url)
        self.assertEqual(res.status_code, 204)
        self.assertTrue(Document.all_objects.filter(id=self.doc.id).exists())
        self.assertFalse(Document.objects.filter(id=self.doc.id).exists())


class DocumentDownloadTests(_BaseDocTestCase):
    def setUp(self):
        super().setUp()
        self.doc = Document.objects.create(
            title="A", doc_type=DocType.UMK, user=self.teacher,
            department=self.dept, file_path="/u/x.pdf", mime_type="application/pdf",
            file_size=2048, academic_year="2025-2026",
        )

    def test_download_returns_metadata(self):
        self._auth(self.dean)
        res = self.client.get(f"{self.url}{self.doc.id}/download/")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data["file_path"], "/u/x.pdf")
        self.assertEqual(res.data["mime_type"], "application/pdf")
        self.assertEqual(res.data["file_size"], 2048)


class UmkStatusTests(_BaseDocTestCase):
    def setUp(self):
        super().setUp()
        self.dept2 = Department.objects.create(name="МАТ", faculty=self.faculty)
        Document.objects.create(
            title="1", doc_type=DocType.UMK, user=self.teacher,
            department=self.dept, file_path="/1", academic_year="2025-2026",
            status=DocumentStatus.APPROVED,
        )
        Document.objects.create(
            title="2", doc_type=DocType.UMK, user=self.teacher,
            department=self.dept, file_path="/2", academic_year="2025-2026",
            status=DocumentStatus.PENDING,
        )
        Document.objects.create(
            title="3", doc_type=DocType.SYLLABUS, user=self.teacher,
            department=self.dept, file_path="/3", academic_year="2025-2026",
        )

    def test_teacher_forbidden(self):
        self._auth(self.teacher)
        res = self.client.get(f"{self.url}umk/status/")
        self.assertEqual(res.status_code, 403)

    def test_vice_rector_sees_counts(self):
        self._auth(self.vice)
        res = self.client.get(f"{self.url}umk/status/")
        self.assertEqual(res.status_code, 200)
        by_id = {row["department"]: row for row in res.data}
        self.assertEqual(by_id[str(self.dept.id)]["total"], 2)
        self.assertEqual(by_id[str(self.dept.id)]["approved"], 1)
        self.assertEqual(by_id[str(self.dept.id)]["pending"], 1)
        self.assertEqual(by_id[str(self.dept2.id)]["total"], 0)
