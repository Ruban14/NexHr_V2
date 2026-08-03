#!/usr/bin/env python3
"""Report assets with warranty expiring soon or already expired.

Cron example (daily at 07:15):
  15 7 * * * cd /path/to/Backend && python scripts/check_asset_warranty_expiry.py --days 30
"""

from __future__ import annotations

import json
import sys
from datetime import timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _bootstrap import base_parser, parse_date, setup_django  # noqa: E402


def main() -> int:
    parser = base_parser('List assets with expired / soon-to-expire warranty.')
    parser.add_argument(
        '--days',
        type=int,
        default=30,
        help='Include warranties expiring within this many days (default: 30).',
    )
    args = parser.parse_args()
    setup_django()

    from django.db.models import Q
    from django.utils import timezone

    from apps.assets.models import Asset

    day = parse_date(args.date) or timezone.localdate()
    until = day + timedelta(days=max(args.days, 0))

    qs = (
        Asset.objects.filter(is_active=True, warranty_expiry__isnull=False)
        .filter(Q(warranty_expiry__lte=until))
        .select_related('organization', 'asset_type')
        .order_by('warranty_expiry')
    )
    if args.organization_id:
        qs = qs.filter(organization_id=args.organization_id)

    rows = []
    for asset in qs.iterator():
        status = 'expired' if asset.warranty_expiry < day else 'expiring'
        rows.append(
            {
                'status': status,
                'warranty_expiry': asset.warranty_expiry.isoformat(),
                'organization_id': str(asset.organization_id),
                'asset_id': str(asset.id),
                'name': asset.name,
                'asset_code': asset.asset_code or '',
                'asset_type': getattr(asset.asset_type, 'name', None) if asset.asset_type_id else None,
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
            label = row['asset_code'] or row['name']
            print(f'  [{row["status"]}] {row["warranty_expiry"]} · {label} · {row["asset_type"]}')
        if len(rows) > 50:
            print(f'  … {len(rows) - 50} more')

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
