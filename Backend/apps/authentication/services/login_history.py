"""Login history audit logging."""

from __future__ import annotations

from typing import Any

from apps.authentication.models import LoginHistory, User
from apps.authentication.services.device import DeviceInfo


class LoginHistoryService:
    """Append-only login event recorder."""

    @staticmethod
    def record(
        *,
        email: str,
        event_type: str,
        user: User | None = None,
        device: DeviceInfo | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> LoginHistory:
        """Persist a login-related audit event."""
        return LoginHistory.objects.create(
            user=user,
            email=email.lower(),
            event_type=event_type,
            ip_address=device.ip_address if device else None,
            user_agent=device.user_agent if device else '',
            device_name=device.device_name if device else '',
            metadata=metadata or {},
        )
