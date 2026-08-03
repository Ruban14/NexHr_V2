# Scheduler scripts

Runnable jobs for cron / systemd timers. Run from the `Backend` directory with the project venv active.

## Scripts

| Script | Purpose | Suggested schedule |
|--------|---------|-------------------|
| `allocate_monthly_leaves.py` | Credit leave for rules with `allocation_frequency=monthly` | `0 1 1 * *` (1st of month) |
| `allocate_quarterly_leaves.py` | Credit leave for `quarterly` rules | `10 1 1 1,4,7,10 *` |
| `carry_forward_leaves.py` | Year-end carry-forward (before yearly credit) | `0 1 1 1 *` |
| `allocate_yearly_leaves.py` | Credit leave for `yearly` rules | `20 1 1 1 *` |
| `check_document_expiry.py` | Report expired / soon-expiring documents | `0 7 * * *` |
| `check_asset_warranty_expiry.py` | Report expired / soon-expiring asset warranties | `15 7 * * *` |

## Common flags

```bash
python scripts/allocate_monthly_leaves.py --dry-run
python scripts/allocate_monthly_leaves.py --organization-id <uuid>
python scripts/allocate_monthly_leaves.py --date 2026-07-01 --json
python scripts/check_document_expiry.py --days 30
```

- `--dry-run` — preview without writing balances/logs (allocation & carry-forward only)
- `--organization-id` — limit to one org
- `--date YYYY-MM-DD` — run as-of a specific date
- `--json` — machine-readable summary

## Example crontab

```cron
# Leave allocation
0 1 1 * *        cd /path/to/Backend && /path/to/venv/bin/python scripts/allocate_monthly_leaves.py >> /var/log/nexhr/leaves-monthly.log 2>&1
10 1 1 1,4,7,10 * cd /path/to/Backend && /path/to/venv/bin/python scripts/allocate_quarterly_leaves.py >> /var/log/nexhr/leaves-quarterly.log 2>&1
0 1 1 1 *        cd /path/to/Backend && /path/to/venv/bin/python scripts/carry_forward_leaves.py >> /var/log/nexhr/leaves-carry.log 2>&1
20 1 1 1 *       cd /path/to/Backend && /path/to/venv/bin/python scripts/allocate_yearly_leaves.py >> /var/log/nexhr/leaves-yearly.log 2>&1

# Expiry reports
0 7 * * *        cd /path/to/Backend && /path/to/venv/bin/python scripts/check_document_expiry.py --days 30 >> /var/log/nexhr/docs-expiry.log 2>&1
15 7 * * *       cd /path/to/Backend && /path/to/venv/bin/python scripts/check_asset_warranty_expiry.py --days 30 >> /var/log/nexhr/asset-warranty.log 2>&1
```

## Behaviour notes

- Allocation and carry-forward are **idempotent** per period via leave log remarks (`scheduler:monthly:2026-07`, `scheduler:carry_forward:2025`, …).
- Monthly/quarterly credits respect each rule’s `annual_limit`.
- Only active employees (non-terminal lifecycle) with a matching leave policy are processed.
- Year-end order: **carry-forward first**, then **yearly allocation**.
