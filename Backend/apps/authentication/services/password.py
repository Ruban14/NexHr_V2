"""Password reset token lifecycle."""

from __future__ import annotations

from datetime import timedelta

from django.conf import settings
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from django.utils import timezone

from apps.authentication.models import PasswordReset, User
from apps.authentication.services.email import EmailService
from apps.authentication.services.login_attempt import LoginAttemptService
from apps.authentication.services.session import SessionService
from apps.core.crypto import constant_time_compare, generate_secure_token, hash_token
from apps.core.exceptions import TokenInvalidError, ValidationServiceError


class PasswordService:
    """Handle forgot-password and reset-password flows."""

    GENERIC_FORGOT_MESSAGE = (
        'If an account exists for that email address, password reset instructions have been sent.'
    )

    @staticmethod
    def _expires_at() -> timezone.datetime:
        return timezone.now() + timedelta(hours=settings.AUTH_PASSWORD_RESET_HOURS)

    @classmethod
    def _invalidate_active(cls, user: User) -> None:
        PasswordReset.objects.filter(user=user, is_active=True).update(is_active=False)

    @classmethod
    @transaction.atomic
    def request_reset(cls, *, email: str, ip_address: str | None) -> str:
        """Create a reset token if the user exists; always return a generic message."""
        normalized_email = email.lower()
        try:
            user = User.objects.get(email=normalized_email, is_active=True)
        except User.DoesNotExist:
            return cls.GENERIC_FORGOT_MESSAGE

        cls._invalidate_active(user)
        raw_token = generate_secure_token()
        PasswordReset.objects.create(
            user=user,
            token_hash=hash_token(raw_token),
            expires_at=cls._expires_at(),
            requested_ip=ip_address,
        )
        EmailService.send_password_reset_email(email=user.email, token=raw_token)
        return cls.GENERIC_FORGOT_MESSAGE

    @classmethod
    def _find_usable(cls, raw_token: str) -> PasswordReset | None:
        token_hash = hash_token(raw_token)
        return (
            PasswordReset.objects.select_related('user')
            .filter(token_hash=token_hash, is_active=True)
            .order_by('-created_at')
            .first()
        )

    @classmethod
    @transaction.atomic
    def reset_password(cls, *, raw_token: str, new_password: str) -> User:
        """Reset a user's password using a valid bearer token."""
        record = cls._find_usable(raw_token)
        if record is None or not record.is_usable:
            raise TokenInvalidError(message='Reset token is invalid or expired.')

        if not constant_time_compare(hash_token(raw_token), record.token_hash):
            raise TokenInvalidError(message='Reset token is invalid or expired.')

        user = record.user
        try:
            validate_password(new_password, user=user)
        except DjangoValidationError as exc:
            raise ValidationServiceError(
                message='Password validation failed.',
                details={'password': list(exc.messages)},
            ) from exc

        user.set_password(new_password)
        if user.is_locked:
            user.locked_until = None
        user.save(update_fields=['password', 'locked_until', 'updated_at'])
        LoginAttemptService.clear_failures_for_email(email=user.email)

        record.used_at = timezone.now()
        record.is_active = False
        record.save(update_fields=['used_at', 'is_active', 'updated_at'])

        SessionService.deactivate_all_for_user(user)
        return user

    @classmethod
    @transaction.atomic
    def change_password(cls, *, user: User, current_password: str, new_password: str) -> User:
        """Change password for an authenticated user (first-login or settings)."""
        if not user.check_password(current_password):
            raise ValidationServiceError(
                message='Current password is incorrect.',
                code='invalid_current_password',
                details={'current_password': ['Current password is incorrect.']},
            )

        if current_password == new_password:
            raise ValidationServiceError(
                message='Choose a different password from your temporary one.',
                code='password_unchanged',
                details={'password': ['New password must be different from the current password.']},
            )

        try:
            validate_password(new_password, user=user)
        except DjangoValidationError as exc:
            raise ValidationServiceError(
                message='Password validation failed.',
                details={'password': list(exc.messages)},
            ) from exc

        user.set_password(new_password)
        user.must_change_password = False
        if user.is_locked:
            user.locked_until = None
        user.save(update_fields=['password', 'must_change_password', 'locked_until', 'updated_at'])
        LoginAttemptService.clear_failures_for_email(email=user.email)
        return user
