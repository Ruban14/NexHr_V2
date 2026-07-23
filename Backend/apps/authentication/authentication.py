"""JWT authentication with active session validation."""

from __future__ import annotations

from django.utils import timezone
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken

from apps.authentication.models import UserSession


class SessionJWTAuthentication(JWTAuthentication):
    """Reject access tokens tied to revoked or expired sessions."""

    def get_user(self, validated_token):
        user = super().get_user(validated_token)
        session_id = validated_token.get('sid')
        if not session_id:
            raise InvalidToken('Session claim is required.')

        session = (
            UserSession.objects.filter(
                id=session_id,
                user_id=user.id,
                is_active=True,
                expires_at__gt=timezone.now(),
            )
            .only('id')
            .first()
        )
        if session is None:
            raise InvalidToken('Session revoked or expired.')
        return user
