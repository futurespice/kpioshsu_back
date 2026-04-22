from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.views import exception_handler


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is None:
        return None

    if isinstance(exc, ValidationError):
        response.status_code = status.HTTP_422_UNPROCESSABLE_ENTITY

    details = response.data if isinstance(response.data, (dict, list)) else {}
    response.data = {
        "error": str(exc),
        "code": exc.__class__.__name__.upper(),
        "details": details,
    }
    return response
