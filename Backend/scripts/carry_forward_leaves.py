#!/usr/bin/env python3
"""Apply year-end leave carry-forward for policy rules that allow it.

Resets used leave and keeps remaining balance up to carry_forward_limit.
Typically run on 1 Jan before yearly allocation.

Cron example (1 Jan at 01:00):
  0 1 1 1 * cd /path/to/Backend && python scripts/carry_forward_leaves.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _bootstrap import base_parser, parse_date, print_summary, setup_django  # noqa: E402


def main() -> int:
    parser = base_parser('Run leave carry-forward scheduler.')
    args = parser.parse_args()
    setup_django()

    from apps.organization.services.leave_scheduler import LeaveSchedulerService

    summary = LeaveSchedulerService.run_carry_forward(
        on_date=parse_date(args.date),
        organization_id=args.organization_id,
        dry_run=args.dry_run,
    )
    print_summary(summary, as_json=args.json)
    return 1 if summary.get('errors') else 0


if __name__ == '__main__':
    raise SystemExit(main())
