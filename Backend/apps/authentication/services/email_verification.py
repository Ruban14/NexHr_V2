"""Email verification token lifecycle."""

from __future__ import annotations

from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from apps.authentication.models import EmailVerification, User
from apps.authentication.services.email import EmailService
from apps.core.crypto import constant_time_compare, generate_secure_token, hash_token
from apps.core.exceptions import ConflictServiceError, TokenInvalidError, ValidationServiceError


class EmailVerificationService:
    """Issue, validate, and consume email verification tokens."""

    @staticmethod
    def _expires_at() -> timezone.datetime:
        return timezone.now() + timedelta(hours=settings.AUTH_EMAIL_VERIFICATION_HOURS)

    @classmethod
    def _invalidate_active(cls, user: User) -> None:
        EmailVerification.objects.filter(user=user, is_active=True).update(is_active=False)

    @classmethod
    @transaction.atomic
    def create_and_send(cls, user: User) -> None:
        """Create a verification token and email it to the user."""
        if user.is_email_verified:
            raise ConflictServiceError(message='Email is already verified.')

        cls._invalidate_active(user)
        raw_token = generate_secure_token()
        EmailVerification.objects.create(
            user=user,
            token_hash=hash_token(raw_token),
            expires_at=cls._expires_at(),
        )
        EmailService.send_verification_email(email=user.email, token=raw_token)

    @classmethod
    def _find_usable(cls, raw_token: str) -> EmailVerification | None:
        token_hash = hash_token(raw_token)
        return (
            EmailVerification.objects.select_related('user')
            .filter(token_hash=token_hash, is_active=True)
            .order_by('-created_at')
            .first()
        )

    @classmethod
    @transaction.atomic
    def verify(cls, raw_token: str) -> User:
        """Verify a user's email using the provided bearer token."""
        record = cls._find_usable(raw_token)
        if record is None or not record.is_usable:
            raise TokenInvalidError(message='Verification token is invalid or expired.')

        if not constant_time_compare(hash_token(raw_token), record.token_hash):
            raise TokenInvalidError(message='Verification token is invalid or expired.')

        user = record.user
        user.is_email_verified = True
        user.save(update_fields=['is_email_verified', 'updated_at'])

        record.used_at = timezone.now()
        record.is_active = False
        record.save(update_fields=['used_at', 'is_active', 'updated_at'])
        return user

    @classmethod
    @transaction.atomic
    def resend(cls, *, email: str) -> None:
        """Resend verification email if the account exists and is unverified."""
        try:
            user = User.objects.get(email=email.lower())
        except User.DoesNotExist:
            return

        if user.is_email_verified:
            raise ValidationServiceError(message='Email is already verified.')

        cls.create_and_send(user)
