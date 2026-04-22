from io import BytesIO

from django.http import HttpResponse
from openpyxl import Workbook
from rest_framework.exceptions import APIException, ValidationError


XLSX_CONTENT_TYPE = (
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)


class PDFNotImplemented(APIException):
    status_code = 501
    default_detail = "PDF export не реализован (контракт согласовывается — ТЗ v2 §14)"
    default_code = "NOT_IMPLEMENTED"


def require_xlsx(request):
    """Возвращает 'xlsx' или бросает APIException/ValidationError."""
    fmt = request.query_params.get("format", "xlsx").lower()
    if fmt == "xlsx":
        return fmt
    if fmt == "pdf":
        raise PDFNotImplemented()
    raise ValidationError({"format": "Допустимые значения: xlsx, pdf"})


def xlsx_response(headers, rows, filename):
    wb = Workbook()
    ws = wb.active
    ws.append(headers)
    for row in rows:
        ws.append(list(row))
    buf = BytesIO()
    wb.save(buf)
    response = HttpResponse(buf.getvalue(), content_type=XLSX_CONTENT_TYPE)
    response["Content-Disposition"] = f'attachment; filename="{filename}.xlsx"'
    return response
