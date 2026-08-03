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
import type { AttendanceRecord } from '../../types';
import { useWorkspace } from '../../workspace/WorkspaceContext';
import './AttendanceApprovalsPage.css';

type StatusFilter = 'pending' | 'approved' | 'rejected' | 'all';

const FILTERS: { value: StatusFilter; label: string }[] = [
  { value: 'pending', label: 'Pending' },
  { value: 'approved', label: 'Approved' },
  { value: 'rejected', label: 'Rejected' },
  { value: 'all', label: 'All' },
];

const APPROVAL_LABELS: Record<string, string> = {
  pending: 'Pending',
  approved: 'Approved',
  rejected: 'Rejected',
};

function approvalClass(status?: string | null): string {
  if (status === 'approved') return 'is-ok';
  if (status === 'pending') return 'is-warn';
  if (status === 'rejected') return 'is-bad';
  return 'is-muted';
}

function formatTime(value?: string | null): string {
  if (!value) return '—';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit' });
}

function formatHours(value?: string | null): string {
  if (value == null || value === '') return '—';
  const num = Number(value);
  if (Number.isNaN(num)) return value;
  return `${num.toFixed(2)} h`;
}

function formatDate(value?: string | null): string {
  if (!value) return '—';
  const date = new Date(`${value}T00:00:00`);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleDateString(undefined, {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  });
}

function nameInitials(name?: string | null, code?: string | null): string {
  const parts = (name || '').trim().split(/\s+/).filter(Boolean);
  if (parts.length >= 2) return `${parts[0][0]}${parts[1][0]}`.toUpperCase();
  if (parts.length === 1 && parts[0].length >= 2) return parts[0].slice(0, 2).toUpperCase();
  const fromCode = (code || '').replace(/[^A-Za-z0-9]/g, '');
  if (fromCode.length >= 2) return fromCode.slice(0, 2).toUpperCase();
  return 'EM';
}

export function AttendanceApprovalsPage() {
  const { currentBranch } = useWorkspace();
  const [items, setItems] = useState<AttendanceRecord[]>([]);
  const [pendingCount, setPendingCount] = useState(0);
  const [filter, setFilter] = useState<StatusFilter>('pending');
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [actionId, setActionId] = useState<string | null>(null);
  const [detailRow, setDetailRow] = useState<AttendanceRecord | null>(null);
  const [rejectRow, setRejectRow] = useState<AttendanceRecord | null>(null);
  const [rejectRemarks, setRejectRemarks] = useState('');

  const load = useCallback(async () => {
    const token = tokenStorage.getAccessToken();
    if (!token) return;
    setLoading(true);
    setError(null);
    try {
      const data = await organizationApi.listAttendanceApprovals(token, filter);
      setItems(data.items);
      setPendingCount(data.pending_count);
    } catch (err) {
      setError(extractErrorMessage(err, 'Unable to load attendance approvals.'));
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
      const haystack = [row.employee_name, row.employee_code, row.remarks, row.approval_status]
        .filter(Boolean)
        .join(' ')
        .toLowerCase();
      return haystack.includes(query);
    });
  }, [items, search]);

  async function review(row: AttendanceRecord, approve: boolean, remarks = '') {
    const token = tokenStorage.getAccessToken();
    if (!token || !row.id) return;
    setActionId(row.id);
    setError(null);
    try {
      await organizationApi.reviewAttendanceApproval(token, row.id, {
        approve,
        remarks: remarks.trim(),
      });
      const name = row.employee_name || 'Employee';
      setSuccess(approve ? `Approved attendance for ${name}.` : `Rejected attendance for ${name}.`);
      setDetailRow(null);
      setRejectRow(null);
      setRejectRemarks('');
      await load();
    } catch (err) {
      setError(extractErrorMessage(err, 'Unable to review attendance entry.'));
    } finally {
      setActionId(null);
    }
  }

  const columns = useMemo<DataTableColumn<AttendanceRecord>[]>(
    () => [
      {
        key: 'employee',
        header: 'Employee',
        render: (row) => (
          <div className="att-approvals__person">
            <span className="att-approvals__avatar" aria-hidden>
              {nameInitials(row.employee_name, row.employee_code)}
            </span>
            <div>
              <Link className="att-approvals__employee" to={`/app/employees/${row.employee_id}`}>
                {row.employee_name || 'Employee'}
              </Link>
              <span className="att-approvals__muted">{row.employee_code || '—'}</span>
            </div>
          </div>
        ),
      },
      {
        key: 'date',
        header: 'Date',
        width: '120px',
        render: (row) => formatDate(row.attendance_date),
      },
      {
        key: 'session',
        header: 'Session',
        width: '160px',
        render: (row) => {
          const session = row.sessions?.find((item) => item.source === 'manual') || row.sessions?.[0];
          return (
            <span>
              {formatTime(session?.check_in || row.first_check_in)} –{' '}
              {formatTime(session?.check_out || row.last_check_out)}
            </span>
          );
        },
      },
      {
        key: 'worked',
        header: 'Worked',
        width: '90px',
        render: (row) => formatHours(row.total_worked_hours),
      },
      {
        key: 'reason',
        header: 'Reason',
        render: (row) => <div className="att-approvals__reason">{row.remarks || '—'}</div>,
      },
      {
        key: 'status',
        header: 'Status',
        width: '120px',
        render: (row) => (
          <span className={`att-approvals__status ${approvalClass(row.approval_status)}`}>
            {APPROVAL_LABELS[row.approval_status || ''] || row.approval_status || '—'}
          </span>
        ),
      },
      {
        key: 'actions',
        header: '',
        width: '120px',
        render: (row) => {
          const busy = actionId === row.id;
          return (
            <div className="att-approvals__actions" onClick={(event) => event.stopPropagation()}>
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
                    onClick={() => {
                      setRejectRow(row);
                      setRejectRemarks('');
                    }}
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
    <section className="att-approvals">
      <PageHeader
        title="Attendance approvals"
        description="Review manual entries and missing-logout adjustments from your team."
        actions={
          pendingCount ? (
            <span className="att-approvals__pending-pill">{pendingCount} pending</span>
          ) : null
        }
      />

      <Toolbar
        left={
          <div className="att-approvals__toolbar">
            <div className="att-approvals__filters" role="tablist" aria-label="Status filter">
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
              className="att-approvals__search"
              value={search}
              onValueChange={setSearch}
              placeholder="Search employee…"
            />
          </div>
        }
        right={
          <Button type="button" variant="secondary" onClick={() => void load()} disabled={loading}>
            Refresh
          </Button>
        }
      />

      {error ? <p className="att-approvals__banner att-approvals__banner--error">{error}</p> : null}
      {success ? (
        <p className="att-approvals__banner att-approvals__banner--success">{success}</p>
      ) : null}

      {loading ? (
        <LoadingSkeleton rows={6} />
      ) : (
        <DataTable
          columns={columns}
          rows={visibleItems}
          empty={
            <EmptyState
              title={filter === 'pending' ? 'No pending entries' : 'No entries found'}
              description="Manual attendance submissions from your reports appear here."
            />
          }
        />
      )}

      <Modal
        open={Boolean(detailRow)}
        title="Manual attendance"
        onClose={() => setDetailRow(null)}
        footer={
          detailRow?.can_review ? (
            <>
              <Button type="button" variant="ghost" onClick={() => setDetailRow(null)}>
                Close
              </Button>
              <Button
                type="button"
                variant="ghost"
                onClick={() => {
                  setRejectRow(detailRow);
                  setRejectRemarks('');
                }}
              >
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
          <div className="att-approvals__detail">
            <dl className="att-approvals__detail-grid">
              <div>
                <dt>Employee</dt>
                <dd>{detailRow.employee_name || '—'}</dd>
              </div>
              <div>
                <dt>Date</dt>
                <dd>{formatDate(detailRow.attendance_date)}</dd>
              </div>
              <div>
                <dt>Worked</dt>
                <dd>{formatHours(detailRow.total_worked_hours)}</dd>
              </div>
              <div>
                <dt>Status</dt>
                <dd>
                  <span className={`att-approvals__status ${approvalClass(detailRow.approval_status)}`}>
                    {APPROVAL_LABELS[detailRow.approval_status || ''] || detailRow.approval_status}
                  </span>
                </dd>
              </div>
            </dl>
            <ul className="att-approvals__sessions">
              {(detailRow.sessions || []).map((session) => (
                <li key={session.id}>
                  <strong>
                    {formatTime(session.check_in)} – {formatTime(session.check_out)}
                  </strong>
                  <span>
                    {formatHours(session.worked_hours)} · {session.source}
                  </span>
                </li>
              ))}
            </ul>
            {detailRow.remarks ? (
              <div className="att-approvals__reason-block">
                <span>Reason</span>
                <p>{detailRow.remarks}</p>
              </div>
            ) : null}
          </div>
        ) : null}
      </Modal>

      <Modal
        open={Boolean(rejectRow)}
        title="Reject manual attendance"
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
          <div className="att-approvals__reject">
            <p>
              Reject manual attendance for <strong>{rejectRow.employee_name || 'this employee'}</strong>{' '}
              on {formatDate(rejectRow.attendance_date)}.
            </p>
            <label>
              <span>Reason for rejection</span>
              <textarea
                rows={3}
                value={rejectRemarks}
                autoFocus
                onChange={(event) => setRejectRemarks(event.target.value)}
              />
            </label>
          </div>
        ) : null}
      </Modal>
    </section>
  );
}
