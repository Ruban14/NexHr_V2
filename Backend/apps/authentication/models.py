"""Authentication and identity models."""

from __future__ import annotations

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone

from apps.authentication.managers import UserManager
from apps.core.models import TimeStampedModel, UUIDModel


class User(AbstractBaseUser, PermissionsMixin, UUIDModel, TimeStampedModel):
    """Email-based user account."""

    email = models.EmailField(unique=True, db_index=True)
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_email_verified = models.BooleanField(default=False)
    must_change_password = models.BooleanField(default=False, db_index=True)
    locked_until = models.DateTimeField(null=True, blank=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS: list[str] = []

    class Meta:
        verbose_name = 'user'
        verbose_name_plural = 'users'
        ordering = ['-created_at']

    def __str__(self) -> str:
        return self.email

    @property
    def full_name(self) -> str:
        """Return the user's display name."""
        return f'{self.first_name} {self.last_name}'.strip()

    @property
    def is_locked(self) -> bool:
        """Return whether the account is currently locked."""
        return self.locked_until is not None and self.locked_until > timezone.now()

    def lock(self, until: timezone.datetime) -> None:
        """Lock the account until the given timestamp."""
        self.locked_until = until
        self.save(update_fields=['locked_until', 'updated_at'])

    def unlock(self) -> None:
        """Clear any active account lock."""
        self.locked_until = None
        self.save(update_fields=['locked_until', 'updated_at'])


class UserSession(UUIDModel, TimeStampedModel):
    """Tracks an authenticated refresh-token session."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='sessions',
    )
    refresh_token_hash = models.CharField(max_length=64, db_index=True)
    refresh_jti = models.CharField(max_length=64, blank=True, db_index=True)
    device_name = models.CharField(max_length=255, blank=True)
    device_type = models.CharField(max_length=64, blank=True)
    browser = models.CharField(max_length=128, blank=True)
    os = models.CharField(max_length=128, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    last_used_at = models.DateTimeField(default=timezone.now)
    expires_at = models.DateTimeField()

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['refresh_token_hash']),
        ]

    def __str__(self) -> str:
        return f'Session {self.id} for {self.user.email}'


class LoginHistory(UUIDModel, TimeStampedModel):
    """Append-only login audit trail."""

    class EventType(models.TextChoices):
        LOGIN_SUCCESS = 'login_success', 'Login success'
        LOGIN_FAILURE = 'login_failure', 'Login failure'
        LOGOUT = 'logout', 'Logout'
        TOKEN_REFRESH = 'token_refresh', 'Token refresh'

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='login_history',
    )
    email = models.EmailField(db_index=True)
    event_type = models.CharField(max_length=32, choices=EventType.choices)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    device_name = models.CharField(max_length=255, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        verbose_name_plural = 'login histories'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['email', 'created_at']),
            models.Index(fields=['user', 'created_at']),
        ]

    def __str__(self) -> str:
        return f'{self.event_type} - {self.email}'


class EmailVerification(UUIDModel, TimeStampedModel):
    """Stores hashed email verification tokens."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='email_verifications',
    )
    token_hash = models.CharField(max_length=64, db_index=True)
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['token_hash', 'is_active']),
        ]

    def __str__(self) -> str:
        return f'EmailVerification for {self.user.email}'

    @property
    def is_expired(self) -> bool:
        return timezone.now() >= self.expires_at

    @property
    def is_usable(self) -> bool:
        return self.is_active and not self.is_expired and self.used_at is None


class PasswordReset(UUIDModel, TimeStampedModel):
    """Stores hashed password reset tokens."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='password_resets',
    )
    token_hash = models.CharField(max_length=64, db_index=True)
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    requested_ip = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['token_hash', 'is_active']),
        ]

    def __str__(self) -> str:
        return f'PasswordReset for {self.user.email}'

    @property
    def is_expired(self) -> bool:
        return timezone.now() >= self.expires_at

    @property
    def is_usable(self) -> bool:
        return self.is_active and not self.is_expired and self.used_at is None


class LoginAttempt(UUIDModel, TimeStampedModel):
    """Tracks failed login attempts for brute-force protection."""

    email = models.EmailField(db_index=True)
    ip_address = models.GenericIPAddressField(db_index=True)
    succeeded = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['email', 'ip_address', 'created_at']),
        ]

    def __str__(self) -> str:
        status_label = 'success' if self.succeeded else 'failure'
        return f'{status_label} attempt for {self.email} from {self.ip_address}'
