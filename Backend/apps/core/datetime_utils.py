"""Application timezone helpers (IST by default)."""

from __future__ import annotations

from datetime import date, datetime
from zoneinfo import ZoneInfo

from django.conf import settings
from django.utils import timezone


def get_app_timezone() -> ZoneInfo:
    """Return the configured application timezone."""
    return ZoneInfo(getattr(settings, 'APP_TIMEZONE', settings.TIME_ZONE))


def serialize_datetime(value: datetime | None) -> str | None:
    """Serialize an aware datetime in the application timezone (IST)."""
    if value is None:
        return None
    if timezone.is_naive(value):
        value = timezone.make_aware(value, timezone=timezone.utc)
    return value.astimezone(get_app_timezone()).isoformat()


def serialize_date(value: date | None) -> str | None:
    """Serialize a date value."""
    if value is None:
        return None
    return value.isoformat()
