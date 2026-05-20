"""
Custom DRF exception handler.
Returns errors as {"error": "<machine_readable>", "detail": "<human readable>"}
as specified in the report's API error format (Section 7).
"""
from rest_framework.views import exception_handler
from rest_framework.exceptions import APIException
from rest_framework import status


class AlreadyCheckedInError(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = "This ticket has already been checked in."
    default_code = "already_checked_in"


class CapacityExhaustedError(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = "No tickets remaining for this tier."
    default_code = "capacity_exhausted"


class InvalidQRError(APIException):
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = "The QR code is invalid or not found."
    default_code = "invalid_qr"


class PaymentFailedError(APIException):
    status_code = status.HTTP_402_PAYMENT_REQUIRED
    default_detail = "Payment could not be processed."
    default_code = "payment_failed"


class RegistrationNotConfirmedError(APIException):
    status_code = status.HTTP_410_GONE
    default_detail = "Registration is not in CONFIRMED status."
    default_code = "registration_not_confirmed"


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is not None:
        code = getattr(exc, "default_code", "error")
        if hasattr(exc, "get_codes"):
            codes = exc.get_codes()
            if isinstance(codes, str):
                code = codes
            elif isinstance(codes, dict):
                code = list(codes.values())[0]
                if isinstance(code, list):
                    code = code[0]
        detail = response.data.get("detail", str(exc))
        if isinstance(detail, list):
            detail = detail[0] if detail else str(exc)
        response.data = {
            "error": code,
            "detail": str(detail),
        }
    return response
