"""Cryptographic helpers for token hashing and comparison."""

from __future__ import annotations

import hashlib
import hmac
import secrets


def hash_token(raw_token: str) -> str:
    """Return a SHA-256 hex digest of the provided token."""
    return hashlib.sha256(raw_token.encode('utf-8')).hexdigest()


def generate_secure_token(length: int = 32) -> str:
    """Generate a URL-safe random token."""
    return secrets.token_urlsafe(length)


def constant_time_compare(left: str, right: str) -> bool:
    """Compare two strings in constant time."""
    return hmac.compare_digest(left.encode('utf-8'), right.encode('utf-8'))
