"""Consistent JSON API response helpers."""

from __future__ import annotations

from typing import Any

from rest_framework import status
from rest_framework.response import Response


def success_response(
    *,
    data: Any = None,
    message: str = 'Success',
    status_code: int = status.HTTP_200_OK,
) -> Response:
    """Return a standardized success envelope."""
    payload: dict[str, Any] = {
        'success': True,
        'message': message,
        'data': data,
        'errors': None,
    }
    return Response(payload, status=status_code)


def error_response(
    *,
    message: str,
    errors: dict[str, Any] | list[Any] | None = None,
    status_code: int = status.HTTP_400_BAD_REQUEST,
) -> Response:
    """Return a standardized error envelope."""
    payload: dict[str, Any] = {
        'success': False,
        'message': message,
        'data': None,
        'errors': errors,
    }
    return Response(payload, status=status_code)
