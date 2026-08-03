import { useCallback, useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { organizationApi } from '../../api/auth';
import { extractErrorMessage } from '../../api/client';
import { tokenStorage } from '../../auth/tokenStorage';
import { Button } from '../../components/Button';
import { DataTable, type DataTableColumn } from '../../components/ui/DataTable';
import { EmptyState } from '../../components/ui/EmptyState';
import {
  IconAction,
  IconApprove,
  IconReject,
  IconView,
} from '../../components/ui/IconAction';
import { LoadingSkeleton } from '../../components/ui/LoadingSkeleton';
import { Modal } from '../../components/ui/Modal';
import { PageHeader } from '../../components/ui/PageHeader';
import { SearchBar } from '../../components/ui/SearchBar';
import { Toolbar } from '../../components/ui/Toolbar';
import type { LeaveApplication } from '../../types';
import { useWorkspace } from '../../workspace/WorkspaceContext';
import './LeaveApprovalsPage.css';

type StatusFilter = 'pending' | 'approved' | 'rejected' | 'all';

const STATUS_LABELS: Record<string, string> = {
  pending: 'Pending',
  approved: 'Approved',
  rejected: 'Rejected',
  cancelled: 'Cancelled',
};

const FILTERS: { value: StatusFilter; label: string }[] = [
  { value: 'pending', label: 'Pending' },
  { value: 'approved', label: 'Approved' },
  { value: 'rejected', label: 'Rejected' },
  { value: 'all', label: 'All' },
];

function statusClass(status: string): string {
  if (status === 'approved') return 'is-ok';
  if (status === 'pending') return 'is-warn';
  if (status === 'rejected' || status === 'cancelled') return 'is-bad';
  return 'is-muted';
}

function formatDayCount(row: LeaveApplication): string {
  if (row.is_half_day) return 'Half day';
  const num = Number(row.number_of_days);
  if (Number.isNaN(num)) return row.number_of_days;
  const label = Number.isInteger(num) ? String(num) : num.toFixed(1);
  return `${label} day${num === 1 ? '' : 's'}`;
}

function formatAppliedOn(value?: string | null): string {
  if (!value) return '—';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleDateString('en-GB', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  });
}

function formatRange(from?: string | null, to?: string | null): string {
  if (!from) return '—';
  if (!to || to === from) return formatAppliedOn(`${from}T00:00:00`);
  return `${formatAppliedOn(`${from}T00:00:00`)} – ${formatAppliedOn(`${to}T00:00:00`)}`;
}

function nameInitials(name?: string | null, code?: string | null): string {
  const parts = (name || '')
    .trim()
    .split(/\s+/)
    .filter(Boolean);
  if (parts.length >= 2) {
    return `${parts[0][0]}${parts[1][0]}`.toUpperCase();
  }
  if (parts.length === 1 && parts[0].length >= 2) {
    return parts[0].slice(0, 2).toUpperCase();
  }
  const fromCode = (code || '').replace(/[^A-Za-z0-9]/g, '');
  if (fromCode.length >= 2) return fromCode.slice(0, 2).toUpperCase();
  return 'EM';
}

function StackedDate({ value }: { value?: string | null }) {
  if (!value) return <span className="leave-approvals__muted">—</span>;
  const date = new Date(`${value}T00:00:00`);
  if (Number.isNaN(date.getTime())) return <span>{value}</span>;
  return (
    <div className="leave-approvals__stacked-date">
      <span>
        {date.toLocaleDateString('en-GB', {
          day: 'numeric',
          month: 'long',
        })}
      </span>
      <span>{date.getFullYear()}</span>
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  return (
    <span className={`leave-approvals__status ${statusClass(status)}`}>
      {status === 'approved' ? (
        <svg viewBox="0 0 16 16" aria-hidden>
          <path
            fill="currentColor"
            d="M8 1.5a6.5 6.5 0 1 0 0 13 6.5 6.5 0 0 0 0-13Zm3.03 4.72-3.5 3.5a.75.75 0 0 1-1.06 0l-1.5-1.5a.75.75 0 1 1 1.06-1.06L7 7.94l2.97-2.97a.75.75 0 0 1 1.06 1.06Z"
          />
        </svg>
      ) : null}
      {status === 'pending' ? (
        <svg viewBox="0 0 16 16" aria-hidden>
          <path
            fill="currentColor"
            d="M8 1.5a6.5 6.5 0 1 0 0 13 6.5 6.5 0 0 0 0-13ZM8 4a.75.75 0 0 1 .75.75v2.69l1.78 1.78a.75.75 0 1 1-1.06 1.06l-2-2A.75.75 0 0 1 7.25 7.5v-2.75A.75.75 0 0 1 8 4Z"
          />
        </svg>
      ) : null}
      {status === 'rejected' || status === 'cancelled' ? (
        <svg viewBox="0 0 16 16" aria-hidden>
          <path
            fill="currentColor"
            d="M8 1.5a6.5 6.5 0 1 0 0 13 6.5 6.5 0 0 0 0-13Zm2.28 4.22a.75.75 0 0 1 0 1.06L9.06 8l1.22 1.22a.75.75 0 1 1-1.06 1.06L8 9.06 6.78 10.28a.75.75 0 0 1-1.06-1.06L6.94 8 5.72 6.78a.75.75 0 0 1 1.06-1.06L8 6.94l1.22-1.22a.75.75 0 0 1 1.06 0Z"
          />
        </svg>
      ) : null}
      {STATUS_LABELS[status] || status}
    </span>
  );
}

export function LeaveApprovalsPage() {
  const { currentBranch } = useWorkspace();
  const [items, setItems] = useState<LeaveApplication[]>([]);
  const [pendingCount, setPendingCount] = useState(0);
  const [filter, setFilter] = useState<StatusFilter>('pending');
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [actionId, setActionId] = useState<string | null>(null);

  const [detailRow, setDetailRow] = useState<LeaveApplication | null>(null);
  const [rejectRow, setRejectRow] = useState<LeaveApplication | null>(null);
  const [rejectRemarks, setRejectRemarks] = useState('');

  const load = useCallback(async () => {
    const token = tokenStorage.getAccessToken();
    if (!token) return;
    setLoading(true);
    setError(null);
    try {
      const data = await organizationApi.listLeaveApprovals(token, filter);
      setItems(data.items);
      setPendingCount(data.pending_count);
    } catch (err) {
      setError(extractErrorMessage(err, 'Unable to load leave approvals.'));
      setItems([]);
      setPendingCount(0);
    } finally {
      setLoading(false);
    }
  }, [filter]);

  useEffect(() => {
    void load();
  }, [load, currentBranch?.branch_id]);

  useEffect(() => {
    if (!success) return;
    const timer = window.setTimeout(() => setSuccess(null), 3000);
    return () => window.clearTimeout(timer);
  }, [success]);

  const visibleItems = useMemo(() => {
    const query = search.trim().toLowerCase();
    if (!query) return items;
    return items.filter((row) => {
      const haystack = [
        row.employee_name,
        row.employee_code,
        row.employee_designation_name,
        row.leave_type_name,
        row.reason,
      ]
        .filter(Boolean)
        .join(' ')
        .toLowerCase();
      return haystack.includes(query);
    });
  }, [items, search]);

  async function review(row: LeaveApplication, approve: boolean, remarks = '') {
    const token = tokenStorage.getAccessToken();
    if (!token) return;
    setActionId(row.id);
    setError(null);
    try {
      await organizationApi.reviewLeaveApproval(token, row.id, {
        approve,
        remarks: remarks.trim(),
      });
      const name = row.employee_name || 'Employee';
      setSuccess(approve ? `Approved leave for ${name}.` : `Rejected leave for ${name}.`);
      setDetailRow(null);
      setRejectRow(null);
      setRejectRemarks('');
      await load();
    } catch (err) {
      setError(extractErrorMessage(err, 'Unable to review leave request.'));
    } finally {
      setActionId(null);
    }
  }

  function openReject(row: LeaveApplication) {
    setDetailRow(null);
    setRejectRow(row);
    setRejectRemarks('');
  }

  const columns = useMemo<DataTableColumn<LeaveApplication>[]>(
    () => [
      {
        key: 'employee_id',
        header: 'Employee ID',
        width: '110px',
        render: (row) => (
          <span className="leave-approvals__id">{row.employee_code || '—'}</span>
        ),
      },
      {
        key: 'employee',
        header: 'Employee Name',
        width: '220px',
        render: (row) => (
          <div className="leave-approvals__person">
            <span className="leave-approvals__avatar" aria-hidden>
              {nameInitials(row.employee_name, row.employee_code)}
            </span>
            <div className="leave-approvals__person-text">
              <Link className="leave-approvals__employee" to={`/app/employees/${row.employee_id}`}>
                {row.employee_name || 'Employee'}
              </Link>
              <span className="leave-approvals__title">
                {row.employee_designation_name || '—'}
              </span>
            </div>
          </div>
        ),
      },
      {
        key: 'leave_type',
        header: 'Leave Type',
        width: '130px',
        render: (row) => (
          <span className="leave-approvals__type-pill">{row.leave_type_name || '—'}</span>
        ),
      },
      {
        key: 'applied_on',
        header: 'Applied On',
        width: '120px',
        render: (row) => (
          <span className="leave-approvals__applied">{formatAppliedOn(row.created_at)}</span>
        ),
      },
      {
        key: 'leave_from',
        header: 'Leave From',
        width: '110px',
        render: (row) => <StackedDate value={row.from_date} />,
      },
      {
        key: 'leave_to',
        header: 'Leave To',
        width: '110px',
        render: (row) => <StackedDate value={row.to_date} />,
      },
      {
        key: 'days',
        header: 'Days',
        width: '90px',
        render: (row) => <span className="leave-approvals__days">{formatDayCount(row)}</span>,
      },
      {
        key: 'reason',
        header: 'Reason',
        render: (row) => (
          <div className="leave-approvals__reason-cell" title={row.reason}>
            {row.reason || '—'}
          </div>
        ),
      },
      {
        key: 'status',
        header: 'Status',
        width: '120px',
        render: (row) => <StatusBadge status={row.status} />,
      },
      {
        key: 'actions',
        header: '',
        width: '120px',
        render: (row) => {
          const busy = actionId === row.id;
          return (
            <div className="leave-approvals__actions" onClick={(event) => event.stopPropagation()}>
              <IconAction label="View" onClick={() => setDetailRow(row)} disabled={busy}>
                <IconView />
              </IconAction>
              {row.can_review ? (
                <>
                  <IconAction
                    label="Approve"
                    success
                    disabled={Boolean(actionId)}
                    onClick={() => void review(row, true)}
                  >
                    <IconApprove />
                  </IconAction>
                  <IconAction
                    label="Reject"
                    danger
                    disabled={Boolean(actionId)}
                    onClick={() => openReject(row)}
                  >
                    <IconReject />
                  </IconAction>
                </>
              ) : null}
            </div>
          );
        },
      },
    ],
    [actionId],
  );

  return (
    <section className="leave-approvals">
      <PageHeader
        title="Leave approvals"
        description="Review leave requests from your team in a simple table."
        actions={
          pendingCount ? (
            <span className="leave-approvals__pending-pill">{pendingCount} pending</span>
          ) : null
        }
      />

      <Toolbar
        left={
          <div className="leave-approvals__toolbar">
            <div className="leave-approvals__filters" role="tablist" aria-label="Status filter">
              {FILTERS.map((item) => (
                <button
                  key={item.value}
                  type="button"
                  role="tab"
                  aria-selected={filter === item.value}
                  className={filter === item.value ? 'is-active' : ''}
                  onClick={() => setFilter(item.value)}
                >
                  {item.label}
                  {item.value === 'pending' && pendingCount ? <em>{pendingCount}</em> : null}
                </button>
              ))}
            </div>
            <SearchBar
              className="leave-approvals__search"
              value={search}
              onValueChange={setSearch}
              placeholder="Search employee or reason…"
            />
          </div>
        }
        right={
          <Button type="button" variant="secondary" onClick={() => void load()} disabled={loading}>
            Refresh
          </Button>
        }
      />

      {error ? <p className="leave-approvals__banner leave-approvals__banner--error">{error}</p> : null}
      {success ? (
        <p className="leave-approvals__banner leave-approvals__banner--success">{success}</p>
      ) : null}

      {loading ? (
        <LoadingSkeleton rows={6} />
      ) : (
        <div className="leave-approvals__table">
          <DataTable
            columns={columns}
            rows={visibleItems}
            empty={
              <EmptyState
                title={filter === 'pending' ? 'No pending requests' : 'No requests found'}
                description={
                  search.trim()
                    ? 'Try a different search.'
                    : filter === 'pending'
                      ? 'New leave requests from your reports will appear here.'
                      : 'Switch filters to see other requests.'
                }
              />
            }
          />
        </div>
      )}

      <Modal
        open={Boolean(detailRow)}
        title="Leave request"
        onClose={() => setDetailRow(null)}
        footer={
          detailRow?.can_review ? (
            <>
              <Button type="button" variant="ghost" onClick={() => setDetailRow(null)}>
                Close
              </Button>
              <Button type="button" variant="ghost" onClick={() => detailRow && openReject(detailRow)}>
                Reject
              </Button>
              <Button
                type="button"
                loading={actionId === detailRow.id}
                onClick={() => detailRow && void review(detailRow, true)}
              >
                Approve
              </Button>
            </>
          ) : (
            <Button type="button" variant="secondary" onClick={() => setDetailRow(null)}>
              Close
            </Button>
          )
        }
      >
        {detailRow ? (
          <div className="leave-approvals__detail">
            <dl className="leave-approvals__detail-grid">
              <div>
                <dt>Employee</dt>
                <dd>{detailRow.employee_name || '—'}</dd>
              </div>
              <div>
                <dt>Leave type</dt>
                <dd>{detailRow.leave_type_name || '—'}</dd>
              </div>
              <div>
                <dt>Period</dt>
                <dd>{formatRange(detailRow.from_date, detailRow.to_date)}</dd>
              </div>
              <div>
                <dt>Duration</dt>
                <dd>{formatDayCount(detailRow)}</dd>
              </div>
              <div>
                <dt>Status</dt>
                <dd>
                  <StatusBadge status={detailRow.status} />
                </dd>
              </div>
              <div>
                <dt>Requested</dt>
                <dd>{new Date(detailRow.created_at).toLocaleString()}</dd>
              </div>
            </dl>
            <div className="leave-approvals__detail-reason">
              <span>Reason</span>
              <p>{detailRow.reason}</p>
            </div>
            {detailRow.remarks ? (
              <div className="leave-approvals__detail-reason">
                <span>Remarks</span>
                <p>{detailRow.remarks}</p>
              </div>
            ) : null}
          </div>
        ) : null}
      </Modal>

      <Modal
        open={Boolean(rejectRow)}
        title="Reject leave request"
        onClose={() => (!actionId ? setRejectRow(null) : undefined)}
        footer={
          <>
            <Button type="button" variant="ghost" disabled={Boolean(actionId)} onClick={() => setRejectRow(null)}>
              Cancel
            </Button>
            <Button
              type="button"
              variant="secondary"
              loading={Boolean(rejectRow && actionId === rejectRow.id)}
              disabled={!rejectRemarks.trim()}
              onClick={() => rejectRow && void review(rejectRow, false, rejectRemarks)}
            >
              Confirm reject
            </Button>
          </>
        }
      >
        {rejectRow ? (
          <div className="leave-approvals__reject">
            <p>
              Reject <strong>{rejectRow.leave_type_name}</strong> for{' '}
              <strong>{rejectRow.employee_name || 'this employee'}</strong> (
              {formatRange(rejectRow.from_date, rejectRow.to_date)}).
            </p>
            <label className="leave-approvals__remarks-field">
              <span>Reason for rejection</span>
              <textarea
                rows={3}
                value={rejectRemarks}
                autoFocus
                placeholder="Share a clear reason the employee can understand"
                onChange={(event) => setRejectRemarks(event.target.value)}
              />
            </label>
          </div>
        ) : null}
      </Modal>
    </section>
  );
}
