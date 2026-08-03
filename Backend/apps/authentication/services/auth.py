"""Primary authentication workflows."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import uuid

from django.conf import settings
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from django.utils import timezone
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken

from apps.authentication.models import LoginHistory, User
from apps.authentication.services.device import DeviceInfo
from apps.authentication.services.email_verification import EmailVerificationService
from apps.authentication.services.login_attempt import LoginAttemptService
from apps.authentication.services.login_history import LoginHistoryService
from apps.authentication.services.session import SessionService
from apps.core.datetime_utils import serialize_datetime
from apps.core.exceptions import (
    AuthenticationServiceError,
    ConflictServiceError,
    EmailNotVerifiedError,
    InvalidCredentialsError,
    ValidationServiceError,
)


@dataclass(frozen=True)
class AuthTokens:
    """JWT access and refresh token pair."""

    access: str
    refresh: str


@dataclass(frozen=True)
class AuthResult:
    """Authentication outcome including user and tokens."""

    user: User
    tokens: AuthTokens


class AuthService:
    """Registration, login, logout, refresh, and profile access."""

    @staticmethod
    def _read_refresh_jti(refresh_token: str) -> str:
        return str(RefreshToken(refresh_token)['jti'])

    @staticmethod
    def _issue_tokens(user: User, *, session_id: uuid.UUID) -> AuthTokens:
        """Issue access/refresh tokens always bound to a session id (`sid`)."""
        refresh = RefreshToken.for_user(user)
        refresh['sid'] = str(session_id)
        return AuthTokens(access=str(refresh.access_token), refresh=str(refresh))

    @staticmethod
    def _serialize_user(user: User) -> dict[str, Any]:
        return {
            'id': str(user.id),
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'full_name': user.full_name,
            'is_email_verified': user.is_email_verified,
            'must_change_password': user.must_change_password,
            'is_active': user.is_active,
            'date_joined': serialize_datetime(user.created_at),
            'last_login': serialize_datetime(user.last_login),
        }

    @classmethod
    @transaction.atomic
    def register(
        cls,
        *,
        email: str,
        password: str,
        first_name: str = '',
        last_name: str = '',
    ) -> User:
        """Create a new user account and send a verification email."""
        normalized_email = email.lower().strip()
        if User.objects.filter(email=normalized_email).exists():
            raise ConflictServiceError(message='An account with this email already exists.')

        try:
            validate_password(password)
        except DjangoValidationError as exc:
            raise ValidationServiceError(
                message='Password validation failed.',
                details={'password': list(exc.messages)},
            ) from exc

        user = User.objects.create_user(
            email=normalized_email,
            password=password,
            first_name=first_name.strip(),
            last_name=last_name.strip(),
        )
        EmailVerificationService.create_and_send(user)
        return user

    @classmethod
    def login(cls, *, email: str, password: str, device: DeviceInfo) -> AuthResult:
        """Authenticate a user and create a tracked session."""
        normalized_email = email.lower().strip()
        LoginAttemptService.assert_not_locked(email=normalized_email, ip_address=device.ip_address)

        try:
            user = User.objects.get(email=normalized_email)
        except User.DoesNotExist:
            LoginAttemptService.record_attempt(
                email=normalized_email,
                ip_address=device.ip_address,
                succeeded=False,
            )
            raise InvalidCredentialsError from None

        LoginAttemptService.assert_user_not_locked(user)

        if not user.is_email_verified:
            raise EmailNotVerifiedError

        if not user.is_active or not user.check_password(password):
            LoginAttemptService.record_attempt(
                email=normalized_email,
                ip_address=device.ip_address,
                succeeded=False,
            )
            LoginAttemptService.maybe_lock_user(
                user=user,
                email=normalized_email,
                ip_address=device.ip_address,
            )
            raise InvalidCredentialsError

        return cls._complete_login(user=user, normalized_email=normalized_email, device=device)

    @classmethod
    @transaction.atomic
    def _complete_login(cls, *, user: User, normalized_email: str, device: DeviceInfo) -> AuthResult:
        """Finalize a successful login within a transaction."""
        LoginAttemptService.record_attempt(
            email=normalized_email,
            ip_address=device.ip_address,
            succeeded=True,
        )
        LoginAttemptService.clear_failures(email=normalized_email, ip_address=device.ip_address)
        if user.is_locked:
            user.unlock()

        session_id = uuid.uuid4()
        tokens = cls._issue_tokens(user, session_id=session_id)
        SessionService.create_session(
            user=user,
            session_id=session_id,
            refresh_token=tokens.refresh,
            refresh_jti=cls._read_refresh_jti(tokens.refresh),
            device=device,
        )
        LoginHistoryService.record(
            email=normalized_email,
            event_type=LoginHistory.EventType.LOGIN_SUCCESS,
            user=user,
            device=device,
        )
        user.last_login = timezone.now()
        user.save(update_fields=['last_login'])
        if user.must_change_password:
            from apps.people.services.employee_service import EmployeeService

            EmployeeService.accept_invite_on_login(user=user)
        return AuthResult(user=user, tokens=tokens)

    @classmethod
    @transaction.atomic
    def logout(cls, *, refresh_token: str, device: DeviceInfo | None = None) -> None:
        """Blacklist the refresh token and deactivate its session."""
        session = SessionService.deactivate_by_refresh_token(refresh_token)
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except TokenError:
            if session is None:
                raise AuthenticationServiceError(message='Invalid refresh token.') from None

        if session is not None:
            LoginHistoryService.record(
                email=session.user.email,
                event_type=LoginHistory.EventType.LOGOUT,
                user=session.user,
                device=device,
            )

    @classmethod
    @transaction.atomic
    def refresh(cls, *, refresh_token: str, device: DeviceInfo) -> AuthTokens:
        """Rotate refresh token and update the tracked session."""
        session = SessionService.get_active_by_refresh_token(refresh_token)
        if session is None:
            raise AuthenticationServiceError(message='Session not found or expired.')

        try:
            old_token = RefreshToken(refresh_token)
            user = session.user
            old_token.blacklist()
            new_refresh = RefreshToken.for_user(user)
            new_refresh['sid'] = str(session.id)
            new_tokens = AuthTokens(access=str(new_refresh.access_token), refresh=str(new_refresh))
        except TokenError as exc:
            SessionService.deactivate_session(session)
            raise AuthenticationServiceError(message='Invalid refresh token.') from exc

        SessionService.rotate_session(
            session=session,
            new_refresh_token=new_tokens.refresh,
            refresh_jti=cls._read_refresh_jti(new_tokens.refresh),
            device=device,
        )
        LoginHistoryService.record(
            email=user.email,
            event_type=LoginHistory.EventType.TOKEN_REFRESH,
            user=user,
            device=device,
        )
        return new_tokens

    @classmethod
    def get_profile(cls, user: User) -> dict[str, Any]:
        """Return the authenticated user's profile payload."""
        return cls._serialize_user(user)

    @classmethod
    def build_login_response(cls, result: AuthResult) -> dict[str, Any]:
        """Build login response data."""
        return {
            'user': cls._serialize_user(result.user),
            'tokens': {
                'access': result.tokens.access,
                'refresh': result.tokens.refresh,
            },
        }

    @classmethod
    def build_register_response(cls, user: User) -> dict[str, Any]:
        """Build registration response data without auth tokens."""
        return {
            'user': cls._serialize_user(user),
        }

    @classmethod
    def build_token_response(cls, tokens: AuthTokens) -> dict[str, Any]:
        """Build token-only response data."""
        return {
            'access': tokens.access,
            'refresh': tokens.refresh,
        }
