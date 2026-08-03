#!/usr/bin/env python3
"""Credit yearly leave allocations for all eligible employees.

Cron example (1 Jan at 01:20 — after carry-forward):
  20 1 1 1 * cd /path/to/Backend && python scripts/allocate_yearly_leaves.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _bootstrap import base_parser, parse_date, print_summary, setup_django  # noqa: E402


def main() -> int:
    parser = base_parser('Run yearly leave allocation scheduler.')
    args = parser.parse_args()
    setup_django()

    from apps.leave.models import LeavePolicyRule
    from apps.leave.services.leave_scheduler_service import LeaveSchedulerService

    summary = LeaveSchedulerService.run_allocation(
        frequency=LeavePolicyRule.AllocationFrequency.YEARLY,
        on_date=parse_date(args.date),
        organization_id=args.organization_id,
        dry_run=args.dry_run,
    )
    print_summary(summary, as_json=args.json)
    return 1 if summary.get('errors') else 0


if __name__ == '__main__':
    raise SystemExit(main())
