#!/usr/bin/env python3
"""Credit monthly leave allocations for all eligible employees.

Cron example (1st of every month at 01:00):
  0 1 1 * * cd /path/to/Backend && python scripts/allocate_monthly_leaves.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _bootstrap import base_parser, parse_date, print_summary, setup_django  # noqa: E402


def main() -> int:
    parser = base_parser('Run monthly leave allocation scheduler.')
    args = parser.parse_args()
    setup_django()

    from apps.organization.models import LeavePolicyRule
    from apps.organization.services.leave_scheduler import LeaveSchedulerService

    summary = LeaveSchedulerService.run_allocation(
        frequency=LeavePolicyRule.AllocationFrequency.MONTHLY,
        on_date=parse_date(args.date),
        organization_id=args.organization_id,
        dry_run=args.dry_run,
    )
    print_summary(summary, as_json=args.json)
    return 1 if summary.get('errors') else 0


if __name__ == '__main__':
    raise SystemExit(main())
