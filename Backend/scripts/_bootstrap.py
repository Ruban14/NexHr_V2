"""Shared Django bootstrap for scheduler scripts."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path


def setup_django() -> None:
    """Add Backend to path and configure Django settings."""
    backend_root = Path(__file__).resolve().parent.parent
    if str(backend_root) not in sys.path:
        sys.path.insert(0, str(backend_root))
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'NexHr_V2.settings')
    import django

    django.setup()


def base_parser(description: str) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Compute what would change without writing balances or logs.',
    )
    parser.add_argument(
        '--organization-id',
        default=None,
        help='Limit the job to a single organization UUID.',
    )
    parser.add_argument(
        '--date',
        default=None,
        help='Run as-of date (YYYY-MM-DD). Defaults to today.',
    )
    parser.add_argument(
        '--json',
        action='store_true',
        help='Print summary as JSON.',
    )
    return parser


def parse_date(value: str | None):
    if not value:
        return None
    from datetime import date

    return date.fromisoformat(value)


def print_summary(summary: dict, *, as_json: bool) -> None:
    if as_json:
        print(json.dumps(summary, indent=2, default=str))
        return
    for key, value in summary.items():
        if key == 'errors' and isinstance(value, list):
            print(f'errors: {len(value)}')
            for err in value:
                print(f'  - {err}')
            continue
        print(f'{key}: {value}')
