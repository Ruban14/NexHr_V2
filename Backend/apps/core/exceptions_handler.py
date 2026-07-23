"""Map service and DRF exceptions to the API response envelope."""

from __future__ import annotations

from typing import Any

from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import status
from rest_framework.exceptions import APIException, ValidationError
from rest_framework.views import exception_handler

from apps.core.exceptions import (
    AccountLockedError,
    AuthenticationServiceError,
    ConflictServiceError,
    EmailNotVerifiedError,
    InvalidCredentialsError,
    NotFoundServiceError,
    PermissionDeniedServiceError,
    ServiceError,
    TokenInvalidError,
    ValidationServiceError,
)
from apps.core.responses import error_response


def _service_error_status(exc: ServiceError) -> int:
    if isinstance(exc, AccountLockedError):
        return status.HTTP_429_TOO_MANY_REQUESTS
    if isinstance(exc, InvalidCredentialsError):
        return status.HTTP_401_UNAUTHORIZED
    if isinstance(exc, EmailNotVerifiedError):
        return status.HTTP_403_FORBIDDEN
    if isinstance(exc, AuthenticationServiceError):
        return status.HTTP_401_UNAUTHORIZED
    if isinstance(exc, TokenInvalidError):
        return status.HTTP_400_BAD_REQUEST
    if isinstance(exc, ConflictServiceError):
        return status.HTTP_409_CONFLICT
    if isinstance(exc, NotFoundServiceError):
        return status.HTTP_404_NOT_FOUND
    if isinstance(exc, PermissionDeniedServiceError):
        return status.HTTP_403_FORBIDDEN
    if isinstance(exc, ValidationServiceError):
        return status.HTTP_400_BAD_REQUEST
    return status.HTTP_400_BAD_REQUEST


def custom_exception_handler(exc: Exception, context: dict[str, Any]):
    """Convert exceptions into the NexHR JSON envelope."""
    if isinstance(exc, ServiceError):
        return error_response(
            message=exc.message,
            errors={'code': exc.code, **exc.details},
            status_code=_service_error_status(exc),
        )

    response = exception_handler(exc, context)
    if response is None:
        return None

    if isinstance(exc, ValidationError):
        return error_response(
            message='Validation failed.',
            errors=response.data,
            status_code=response.status_code,
        )

    if isinstance(exc, DjangoValidationError):
        detail = exc.message_dict if hasattr(exc, 'message_dict') else exc.messages
        return error_response(
            message='Validation failed.',
            errors=detail,
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    if isinstance(exc, APIException):
        detail = response.data
        message = detail.get('detail', str(detail)) if isinstance(detail, dict) else str(detail)
        return error_response(
            message=str(message),
            errors=detail if isinstance(detail, (dict, list)) else None,
            status_code=response.status_code,
        )

    return response
