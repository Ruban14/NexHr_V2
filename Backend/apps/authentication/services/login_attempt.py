"""Brute-force protection via login attempt tracking.

IP throttling and account lockout are intentionally separate:

- email+IP failures trigger a temporary throttle for that pair (availability-safe).
- account lock (`User.locked_until`) requires failures from multiple IPs so a
  single attacker IP cannot lock out a known email address.
"""

from __future__ import annotations

from datetime import timedelta

from django.conf import settings
from django.utils import timezone

from apps.authentication.models import LoginAttempt, User
from apps.core.datetime_utils import serialize_datetime
from apps.core.exceptions import AccountLockedError


class LoginAttemptService:
    """Record and evaluate login attempts by email and IP."""

    @staticmethod
    def _window_start() -> timezone.datetime:
        minutes = settings.AUTH_LOCKOUT_WINDOW_MINUTES
        return timezone.now() - timedelta(minutes=minutes)

    @classmethod
    def record_attempt(cls, *, email: str, ip_address: str | None, succeeded: bool) -> None:
        """Persist a login attempt."""
        LoginAttempt.objects.create(
            email=email.lower(),
            ip_address=ip_address or '0.0.0.0',
            succeeded=succeeded,
        )

    @classmethod
    def _failed_count_for_pair(cls, *, email: str, ip_address: str | None) -> int:
        return LoginAttempt.objects.filter(
            email=email.lower(),
            ip_address=ip_address or '0.0.0.0',
            succeeded=False,
            created_at__gte=cls._window_start(),
        ).count()

    @classmethod
    def _failed_count_for_email(cls, *, email: str) -> int:
        return LoginAttempt.objects.filter(
            email=email.lower(),
            succeeded=False,
            created_at__gte=cls._window_start(),
        ).count()

    @classmethod
    def _distinct_failed_ips(cls, *, email: str) -> int:
        return (
            LoginAttempt.objects.filter(
                email=email.lower(),
                succeeded=False,
                created_at__gte=cls._window_start(),
            )
            .values('ip_address')
            .distinct()
            .count()
        )

    @classmethod
    def _locked_account_details(cls, user: User) -> dict[str, str]:
        return {
            'locked_until': serialize_datetime(user.locked_until),
            'recovery_action': 'forgot_password',
        }

    @classmethod
    def assert_not_locked(cls, *, email: str, ip_address: str | None) -> None:
        """Raise if this email/IP pair exceeded the failure threshold (IP throttle)."""
        failed = cls._failed_count_for_pair(email=email, ip_address=ip_address)
        if failed >= settings.AUTH_MAX_LOGIN_ATTEMPTS:
            details: dict[str, int | str] = {
                'retry_after_minutes': settings.AUTH_LOCKOUT_WINDOW_MINUTES,
                'throttle_scope': 'ip',
            }
            try:
                user = User.objects.get(email=email.lower())
            except User.DoesNotExist:
                user = None
            if user is not None and user.is_locked:
                details.update(cls._locked_account_details(user))
            raise AccountLockedError(
                message=(
                    'Too many failed sign-in attempts from this network. '
                    'Try again later or use forgot password.'
                ),
                details=details,
            )

    @classmethod
    def assert_user_not_locked(cls, user: User) -> None:
        """Raise if the user account is actively locked."""
        if user.is_locked:
            raise AccountLockedError(
                message=(
                    'This account is temporarily locked. '
                    'Use forgot password to reset your password and regain access.'
                ),
                details=cls._locked_account_details(user),
            )

    @classmethod
    def maybe_lock_user(cls, *, user: User, email: str, ip_address: str | None) -> None:
        """Lock the user account only when failures span multiple IPs.

        Single-IP brute force is handled by ``assert_not_locked`` (pair throttle)
        and must not lock the victim account (DoS).
        """
        min_ips = int(getattr(settings, 'AUTH_ACCOUNT_LOCK_MIN_IPS', 2))
        email_failures = cls._failed_count_for_email(email=email)
        distinct_ips = cls._distinct_failed_ips(email=email)
        if email_failures >= settings.AUTH_MAX_LOGIN_ATTEMPTS and distinct_ips >= min_ips:
            lock_until = timezone.now() + timedelta(minutes=settings.AUTH_LOCKOUT_DURATION_MINUTES)
            user.lock(lock_until)

    @classmethod
    def clear_failures(cls, *, email: str, ip_address: str | None) -> None:
        """Remove recent failed attempts after a successful login (all IPs for email)."""
        # Successful authentication clears the whole email window to avoid residual lockouts.
        cls.clear_failures_for_email(email=email)

    @classmethod
    def clear_failures_for_email(cls, *, email: str) -> None:
        """Remove recent failed attempts for an email across all IPs."""
        LoginAttempt.objects.filter(
            email=email.lower(),
            succeeded=False,
            created_at__gte=cls._window_start(),
        ).delete()
