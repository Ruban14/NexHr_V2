"""Application-level exception types."""

from __future__ import annotations

from typing import Any


class ServiceError(Exception):
    """Base exception for service-layer failures."""

    default_code: str = 'service_error'
    default_message: str = 'An unexpected error occurred.'

    def __init__(
        self,
        message: str | None = None,
        *,
        code: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        self.message = message or self.default_message
        self.code = code or self.default_code
        self.details = details or {}
        super().__init__(self.message)


class ValidationServiceError(ServiceError):
    """Raised when input fails business validation."""

    default_code = 'validation_error'
    default_message = 'Validation failed.'


class AuthenticationServiceError(ServiceError):
    """Raised for authentication failures."""

    default_code = 'authentication_failed'
    default_message = 'Authentication failed.'


class AccountLockedError(AuthenticationServiceError):
    """Raised when an account or identity is temporarily locked."""

    default_code = 'account_locked'
    default_message = 'Too many failed attempts. Try again later.'


class InvalidCredentialsError(AuthenticationServiceError):
    """Raised when credentials are invalid."""

    default_code = 'invalid_credentials'
    default_message = 'Invalid email or password.'


class EmailNotVerifiedError(AuthenticationServiceError):
    """Raised when a user attempts to sign in before verifying email."""

    default_code = 'email_not_verified'
    default_message = 'Please verify your email address before signing in.'


class TokenInvalidError(ServiceError):
    """Raised when a bearer token is invalid or expired."""

    default_code = 'token_invalid'
    default_message = 'The provided token is invalid or has expired.'


class ConflictServiceError(ServiceError):
    """Raised when a resource conflict occurs."""

    default_code = 'conflict'
    default_message = 'Resource conflict.'


class NotFoundServiceError(ServiceError):
    """Raised when a requested resource does not exist."""

    default_code = 'not_found'
    default_message = 'Resource not found.'


class PermissionDeniedServiceError(ServiceError):
    """Raised when a user lacks permission for an action."""

    default_code = 'permission_denied'
    default_message = 'You do not have permission to perform this action.'
