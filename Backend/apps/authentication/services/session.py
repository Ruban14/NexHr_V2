"""User session lifecycle management."""

from __future__ import annotations

import uuid

from datetime import timedelta

from django.conf import settings
from django.utils import timezone
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken

from apps.authentication.models import User, UserSession
from apps.authentication.services.device import DeviceInfo
from apps.core.crypto import hash_token


class SessionService:
    """Create, rotate, and invalidate refresh-token sessions."""

    @staticmethod
    def _expires_at() -> timezone.datetime:
        return timezone.now() + settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME']

    @classmethod
    def create_session(
        cls,
        *,
        user: User,
        refresh_token: str,
        device: DeviceInfo,
        session_id: uuid.UUID | None = None,
        refresh_jti: str = '',
    ) -> UserSession:
        """Create a new active session for the user."""
        return UserSession.objects.create(
            id=session_id or uuid.uuid4(),
            user=user,
            refresh_token_hash=hash_token(refresh_token),
            refresh_jti=refresh_jti,
            device_name=device.device_name,
            device_type=device.device_type,
            browser=device.browser,
            os=device.os,
            ip_address=device.ip_address,
            user_agent=device.user_agent,
            expires_at=cls._expires_at(),
        )

    @classmethod
    def rotate_session(
        cls,
        *,
        session: UserSession,
        new_refresh_token: str,
        device: DeviceInfo | None = None,
        refresh_jti: str = '',
    ) -> UserSession:
        """Update session metadata after refresh token rotation."""
        session.refresh_token_hash = hash_token(new_refresh_token)
        session.refresh_jti = refresh_jti
        session.last_used_at = timezone.now()
        session.expires_at = cls._expires_at()
        if device is not None:
            session.ip_address = device.ip_address
            session.user_agent = device.user_agent
        session.save(
            update_fields=[
                'refresh_token_hash',
                'refresh_jti',
                'last_used_at',
                'expires_at',
                'ip_address',
                'user_agent',
                'updated_at',
            ],
        )
        return session

    @classmethod
    def get_active_by_refresh_token(cls, refresh_token: str) -> UserSession | None:
        """Find an active session matching the refresh token hash."""
        token_hash = hash_token(refresh_token)
        return (
            UserSession.objects.filter(
                refresh_token_hash=token_hash,
                is_active=True,
                expires_at__gt=timezone.now(),
            )
            .select_related('user')
            .first()
        )

    @classmethod
    def blacklist_session(cls, session: UserSession) -> None:
        """Blacklist the refresh token associated with a session."""
        if not session.refresh_jti:
            return
        try:
            outstanding = OutstandingToken.objects.get(jti=session.refresh_jti)
        except OutstandingToken.DoesNotExist:
            return
        BlacklistedToken.objects.get_or_create(token=outstanding)

    @classmethod
    def deactivate_session(cls, session: UserSession) -> None:
        """Mark a session as inactive."""
        cls.blacklist_session(session)
        session.is_active = False
        session.save(update_fields=['is_active', 'updated_at'])

    @classmethod
    def deactivate_by_refresh_token(cls, refresh_token: str) -> UserSession | None:
        """Deactivate the session associated with a refresh token."""
        session = cls.get_active_by_refresh_token(refresh_token)
        if session is not None:
            cls.deactivate_session(session)
        return session

    @classmethod
    def deactivate_all_for_user(cls, user: User) -> int:
        """Deactivate all active sessions and blacklist their refresh tokens."""
        sessions = list(UserSession.objects.filter(user=user, is_active=True))
        for session in sessions:
            cls.blacklist_session(session)
        # Also blacklist any outstanding refresh tokens not linked via UserSession.
        outstanding = OutstandingToken.objects.filter(user_id=user.id)
        for token in outstanding:
            BlacklistedToken.objects.get_or_create(token=token)
        if not sessions:
            return 0
        return UserSession.objects.filter(
            id__in=[session.id for session in sessions],
        ).update(is_active=False)
