import os

from django.core.exceptions import ValidationError


ALLOWED_UPLOAD_EXTENSIONS = {".pdf", ".docx", ".jpg", ".jpeg", ".png"}
MAX_UPLOAD_SIZE_MB = 50


def validate_oshsu_email(value: str):
    if not value or not value.lower().endswith("@oshsu.kg"):
        raise ValidationError("Email должен заканчиваться на @oshsu.kg")


def validate_upload(file):
    ext = os.path.splitext(file.name)[1].lower()
    if ext not in ALLOWED_UPLOAD_EXTENSIONS:
        allowed = ", ".join(sorted(ALLOWED_UPLOAD_EXTENSIONS))
        raise ValidationError(f"Разрешены только: {allowed}")
    if file.size > MAX_UPLOAD_SIZE_MB * 1024 * 1024:
        raise ValidationError(f"Максимальный размер файла: {MAX_UPLOAD_SIZE_MB} МБ")
