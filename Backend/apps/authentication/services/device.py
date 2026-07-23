"""Parse client device metadata from HTTP requests."""

from __future__ import annotations

from dataclasses import dataclass

from django.http import HttpRequest
from user_agents import parse


@dataclass(frozen=True)
class DeviceInfo:
    """Normalized device metadata extracted from a request."""

    device_name: str
    device_type: str
    browser: str
    os: str
    ip_address: str | None
    user_agent: str


def get_client_ip(request: HttpRequest) -> str | None:
    """Extract the client IP address from request headers."""
    forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if forwarded_for:
        return forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


def parse_device_info(request: HttpRequest) -> DeviceInfo:
    """Build device metadata from the incoming request."""
    user_agent_raw = request.META.get('HTTP_USER_AGENT', '')
    parsed = parse(user_agent_raw)

    device_type = 'desktop'
    if parsed.is_mobile:
        device_type = 'mobile'
    elif parsed.is_tablet:
        device_type = 'tablet'
    elif parsed.is_bot:
        device_type = 'bot'

    device_name = parsed.device.family or 'Unknown device'
    browser = parsed.browser.family or 'Unknown browser'
    os_name = parsed.os.family or 'Unknown OS'

    return DeviceInfo(
        device_name=device_name,
        device_type=device_type,
        browser=browser,
        os=os_name,
        ip_address=get_client_ip(request),
        user_agent=user_agent_raw,
    )
