"""Helpers for organization request context."""

from __future__ import annotations

from rest_framework.request import Request


def get_branch_id(request: Request) -> str | None:
    """Read active branch from X-Branch-Id header or branch_id query param."""
    header = request.headers.get('X-Branch-Id') or request.META.get('HTTP_X_BRANCH_ID')
    if header:
        return str(header).strip() or None
    query = request.query_params.get('branch_id')
    if query:
        return str(query).strip() or None
    return None


def parse_bool(value: str | None) -> bool | None:
    if value is None or value == '':
        return None
    lowered = value.strip().lower()
    if lowered in {'1', 'true', 'yes'}:
        return True
    if lowered in {'0', 'false', 'no'}:
        return False
    return None
