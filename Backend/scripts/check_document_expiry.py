#!/usr/bin/env python3
"""Report employee documents that are expired or expiring soon.

Cron example (daily at 07:00):
  0 7 * * * cd /path/to/Backend && python scripts/check_document_expiry.py --days 30
"""

from __future__ import annotations

import json
import sys
from datetime import timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _bootstrap import base_parser, parse_date, setup_django  # noqa: E402


def main() -> int:
    parser = base_parser('List expired / soon-to-expire employee documents.')
    parser.add_argument(
        '--days',
        type=int,
        default=30,
        help='Include documents expiring within this many days (default: 30).',
    )
    args = parser.parse_args()
    setup_django()

    from django.db.models import Q
    from django.utils import timezone

    from apps.organization.models import EmployeeDocument

    day = parse_date(args.date) or timezone.localdate()
    until = day + timedelta(days=max(args.days, 0))

    qs = (
        EmployeeDocument.objects.filter(expiry_date__isnull=False)
        .filter(Q(expiry_date__lte=until))
        .select_related('employee', 'employee__organization', 'document')
        .order_by('expiry_date')
    )
    if args.organization_id:
        qs = qs.filter(employee__organization_id=args.organization_id)

    rows = []
    for doc in qs.iterator():
        status = 'expired' if doc.expiry_date < day else 'expiring'
        rows.append(
            {
                'status': status,
                'expiry_date': doc.expiry_date.isoformat(),
                'organization_id': str(doc.employee.organization_id),
                'employee_id': str(doc.employee_id),
                'employee': getattr(doc.employee, 'display_name', '') or str(doc.employee_id),
                'document_name': getattr(doc.document, 'name', None),
                'document_id': str(doc.id),
            }
        )

    if args.json:
        print(
            json.dumps(
                {
                    'as_of': day.isoformat(),
                    'until': until.isoformat(),
                    'total': len(rows),
                    'expired': sum(1 for r in rows if r['status'] == 'expired'),
                    'expiring': sum(1 for r in rows if r['status'] == 'expiring'),
                    'items': rows,
                },
                indent=2,
            )
        )
    else:
        expired = sum(1 for r in rows if r['status'] == 'expired')
        expiring = sum(1 for r in rows if r['status'] == 'expiring')
        print(f'as_of: {day.isoformat()}')
        print(f'until: {until.isoformat()}')
        print(f'total: {len(rows)} (expired={expired}, expiring={expiring})')
        for row in rows[:50]:
            print(
                f'  [{row["status"]}] {row["expiry_date"]} · {row["employee"]} · {row["document_name"]}'
            )
        if len(rows) > 50:
            print(f'  … {len(rows) - 50} more')

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
