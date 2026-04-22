from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from apps.common.validators import (
    MAX_UPLOAD_SIZE_MB,
    validate_oshsu_email,
    validate_upload,
)


class ValidateOshsuEmailTests(TestCase):
    def test_valid_email_passes(self):
        validate_oshsu_email("user@oshsu.kg")

    def test_wrong_domain_raises(self):
        with self.assertRaises(ValidationError):
            validate_oshsu_email("user@gmail.com")

    def test_case_insensitive(self):
        validate_oshsu_email("User@OSHSU.KG")

    def test_empty_string_raises(self):
        with self.assertRaises(ValidationError):
            validate_oshsu_email("")

    def test_domain_only_match_not_partial(self):
        # "oshsu.kg.com" is not a oshsu.kg email even though it contains it
        with self.assertRaises(ValidationError):
            validate_oshsu_email("user@oshsu.kg.com")


class ValidateUploadTests(TestCase):
    def test_valid_pdf_passes(self):
        f = SimpleUploadedFile("doc.pdf", b"x", content_type="application/pdf")
        validate_upload(f)

    def test_valid_docx_passes(self):
        f = SimpleUploadedFile("doc.docx", b"x")
        validate_upload(f)

    def test_valid_jpg_passes(self):
        f = SimpleUploadedFile("img.jpg", b"x")
        validate_upload(f)

    def test_valid_png_passes(self):
        f = SimpleUploadedFile("img.png", b"x")
        validate_upload(f)

    def test_invalid_extension_raises(self):
        f = SimpleUploadedFile("evil.exe", b"x")
        with self.assertRaises(ValidationError):
            validate_upload(f)

    def test_oversized_file_raises(self):
        big = b"x" * (MAX_UPLOAD_SIZE_MB * 1024 * 1024 + 1)
        f = SimpleUploadedFile("big.pdf", big)
        with self.assertRaises(ValidationError):
            validate_upload(f)

    def test_extension_is_case_insensitive(self):
        f = SimpleUploadedFile("DOC.PDF", b"x")
        validate_upload(f)
