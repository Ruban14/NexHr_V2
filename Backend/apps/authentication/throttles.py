"""DRF throttling classes for authentication endpoints."""

from __future__ import annotations

from rest_framework.throttling import AnonRateThrottle, SimpleRateThrottle


class AuthAnonRateThrottle(AnonRateThrottle):
    """Throttle unauthenticated auth endpoints."""

    scope = 'auth_anon'


class AuthUserRateThrottle(SimpleRateThrottle):
    """Throttle authenticated auth endpoints per user."""

    scope = 'auth_user'

    def get_cache_key(self, request, view):
        if request.user and request.user.is_authenticated:
            return self.cache_format % {'scope': self.scope, 'ident': request.user.pk}
        return self.get_ident(request)
