import { useCallback, useEffect, useMemo, useState, type FormEvent } from 'react';
import { Link } from 'react-router-dom';
import { organizationApi } from '../../api/auth';
import { extractErrorMessage } from '../../api/client';
import { tokenStorage } from '../../auth/tokenStorage';
import type {
  EmployeeLeaveBalance,
  EmployeeLeaveLog,
  LeaveApplication,
  LeaveType,
} from '../../types';
import { Button } from '../Button';
import { LoadingSkeleton } from '../ui/LoadingSkeleton';
import { Modal } from '../ui/Modal';
import './EmployeeLeavesPanel.css';

type EmployeeLeavesPanelProps = {
  employeeId: string;
};

type LeavesTab = 'overview' | 'requests' | 'activity';

const STATUS_LABELS: Record<string, string> = {
  draft: 'Draft',
  pending: 'Pending',
  approved: 'Approved',
  rejected: 'Rejected',
  cancelled: 'Cancelled',
};

const LOG_LABELS: Record<string, string> = {
  allocation: 'Allocated',
  leave_approved: 'Leave used',
  leave_cancelled: 'Leave restored',
  adjustment: 'Adjusted',
  carry_forward: 'Carried forward',
};

function statusClass(status: string): string {
  if (status === 'approved') return 'is-ok';
  if (status === 'pending') return 'is-warn';
  if (status === 'rejected' || status === 'cancelled') return 'is-bad';
  return 'is-muted';
}

function todayIso(): string {
  return new Date().toISOString().slice(0, 10);
}

function formatDays(value: string | number): string {
  const num = Number(value);
  if (Number.isNaN(num)) return String(value);
  return Number.isInteger(num) ? String(num) : num.toFixed(1);
}

function dayLabel(value: string | number): string {
  const num = Number(value);
  const label = formatDays(value);
  return `${label} day${num === 1 ? '' : 's'}`;
}

function calcRequestedDays(fromDate: string, toDate: string, isHalfDay: boolean): number {
  if (!fromDate) return 0;
  if (isHalfDay) return 0.5;
  const end = toDate || fromDate;
  const startMs = new Date(fromDate).getTime();
  const endMs = new Date(end).getTime();
  if (Number.isNaN(startMs) || Number.isNaN(endMs) || endMs < startMs) return 0;
  return Math.floor((endMs - startMs) / 86400000) + 1;
}

function usagePercent(row: EmployeeLeaveBalance): number {
  const allocated = Number(row.allocated) || 0;
  const used = Number(row.used) || 0;
  if (allocated <= 0) return used > 0 ? 100 : 0;
  return Math.min(100, Math.round((used / allocated) * 100));
}

function formatDateRange(from?: string | null, to?: string | null): string {
  if (!from) return '—';
  if (!to || to === from) return from;
  return `${from} → ${to}`;
}

export function EmployeeLeavesPanel({ employeeId }: EmployeeLeavesPanelProps) {
  const [balances, setBalances] = useState<EmployeeLeaveBalance[]>([]);
  const [applications, setApplications] = useState<LeaveApplication[]>([]);
  const [logs, setLogs] = useState<EmployeeLeaveLog[]>([]);
  const [leaveTypes, setLeaveTypes] = useState<LeaveType[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionLoading, setActionLoading] = useState(false);
  const [tab, setTab] = useState<LeavesTab>('overview');
  const [requestFilter, setRequestFilter] = useState<'all' | 'pending' | 'decided'>('all');
  const [adminOpen, setAdminOpen] = useState(false);

  const [applyOpen, setApplyOpen] = useState(false);
  const [leaveTypeId, setLeaveTypeId] = useState('');
  const [fromDate, setFromDate] = useState(todayIso());
  const [toDate, setToDate] = useState(todayIso());
  const [isHalfDay, setIsHalfDay] = useState(false);
  const [reason, setReason] = useState('');
  const [attachment, setAttachment] = useState<File | null>(null);
  const [applyError, setApplyError] = useState<string | null>(null);

  const [allocateOpen, setAllocateOpen] = useState(false);
  const [allocLeaveTypeId, setAllocLeaveTypeId] = useState('');
  const [allocQuantity, setAllocQuantity] = useState('1');
  const [allocRemarks, setAllocRemarks] = useState('');
  const [allocError, setAllocError] = useState<string | null>(null);

  const pendingCount = useMemo(
    () => applications.filter((row) => row.status === 'pending').length,
    [applications],
  );

  const totalBalance = useMemo(
    () => balances.reduce((sum, row) => sum + (Number(row.balance) || 0), 0),
    [balances],
  );

  const filteredApplications = useMemo(() => {
    if (requestFilter === 'pending') {
      return applications.filter((row) => row.status === 'pending');
    }
    if (requestFilter === 'decided') {
      return applications.filter((row) => row.status !== 'pending' && row.status !== 'draft');
    }
    return applications;
  }, [applications, requestFilter]);

  const requestedDays = calcRequestedDays(fromDate, toDate, isHalfDay);
  const selectedBalance = balances.find((row) => row.leave_type_id === leaveTypeId);

  const load = useCallback(async () => {
    const token = tokenStorage.getAccessToken();
    if (!token) return;
    setLoading(true);
    setError(null);
    try {
      const [balanceRows, applicationRows, logRows, types] = await Promise.all([
        organizationApi.listEmployeeLeaveBalances(token, employeeId),
        organizationApi.listEmployeeLeaveApplications(token, employeeId),
        organizationApi.listEmployeeLeaveLogs(token, employeeId),
        organizationApi.listLeaveTypes(token, { page_size: 100, is_active: true }),
      ]);
      setBalances(balanceRows);
      setApplications(applicationRows);
      setLogs(logRows);
      setLeaveTypes(types.items);
      setLeaveTypeId((prev) => prev || types.items[0]?.id || '');
      setAllocLeaveTypeId((prev) => prev || types.items[0]?.id || '');
    } catch (err) {
      setError(extractErrorMessage(err, 'Unable to load leave data.'));
    } finally {
      setLoading(false);
    }
  }, [employeeId]);

  useEffect(() => {
    void load();
  }, [load]);

  function openApply() {
    setApplyError(null);
    setFromDate(todayIso());
    setToDate(todayIso());
    setIsHalfDay(false);
    setReason('');
    setAttachment(null);
    setLeaveTypeId(leaveTypes[0]?.id || '');
    setApplyOpen(true);
  }

  async function handleApply(event: FormEvent) {
    event.preventDefault();
    const token = tokenStorage.getAccessToken();
    if (!token) return;
    if (!leaveTypeId) {
      setApplyError('Select a leave type.');
      return;
    }
    if (!reason.trim()) {
      setApplyError('Reason is required.');
      return;
    }

    const form = new FormData();
    form.append('leave_type_id', leaveTypeId);
    form.append('from_date', fromDate);
    form.append('to_date', isHalfDay ? fromDate : toDate);
    form.append('is_half_day', isHalfDay ? 'true' : 'false');
    form.append('reason', reason.trim());
    if (attachment) form.append('attachment', attachment);

    setActionLoading(true);
    setApplyError(null);
    try {
      await organizationApi.createEmployeeLeaveApplication(token, employeeId, form);
      setApplyOpen(false);
      setTab('requests');
      await load();
    } catch (err) {
      setApplyError(extractErrorMessage(err, 'Unable to submit leave request.'));
    } finally {
      setActionLoading(false);
    }
  }

  async function handleReview(applicationId: string, approve: boolean) {
    const token = tokenStorage.getAccessToken();
    if (!token) return;
    setActionLoading(true);
    setError(null);
    try {
      await organizationApi.reviewEmployeeLeaveApplication(token, employeeId, applicationId, {
        approve,
      });
      await load();
    } catch (err) {
      setError(extractErrorMessage(err, 'Unable to review leave request.'));
    } finally {
      setActionLoading(false);
    }
  }

  async function handleCancel(applicationId: string) {
    const token = tokenStorage.getAccessToken();
    if (!token) return;
    setActionLoading(true);
    setError(null);
    try {
      await organizationApi.cancelEmployeeLeaveApplication(token, employeeId, applicationId);
      await load();
    } catch (err) {
      setError(extractErrorMessage(err, 'Unable to cancel leave request.'));
    } finally {
      setActionLoading(false);
    }
  }

  async function handleSeed() {
    const token = tokenStorage.getAccessToken();
    if (!token) return;
    setActionLoading(true);
    setError(null);
    setAdminOpen(false);
    try {
      await organizationApi.seedEmployeeLeaveBalances(token, employeeId);
      setTab('overview');
      await load();
    } catch (err) {
      setError(extractErrorMessage(err, 'Unable to seed balances from policy.'));
    } finally {
      setActionLoading(false);
    }
  }

  async function handleAllocate(event: FormEvent) {
    event.preventDefault();
    const token = tokenStorage.getAccessToken();
    if (!token) return;
    if (!allocLeaveTypeId) {
      setAllocError('Select a leave type.');
      return;
    }
    setActionLoading(true);
    setAllocError(null);
    try {
      await organizationApi.allocateEmployeeLeave(token, employeeId, {
        leave_type_id: allocLeaveTypeId,
        quantity: allocQuantity,
        remarks: allocRemarks.trim(),
      });
      setAllocateOpen(false);
      setTab('overview');
      await load();
    } catch (err) {
      setAllocError(extractErrorMessage(err, 'Unable to allocate leave.'));
    } finally {
      setActionLoading(false);
    }
  }

  if (loading) {
    return (
      <article className="emp-profile__card">
        <LoadingSkeleton rows={6} />
      </article>
    );
  }

  return (
    <>
      <article className="emp-profile__card emp-leaves">
        <header className="emp-profile__card-head emp-profile__card-head--row">
          <div>
            <h2>Leaves</h2>
            <p>
              {balances.length
                ? `${formatDays(totalBalance)} days available across ${balances.length} leave type${balances.length === 1 ? '' : 's'}`
                : 'Balances and requests for this employee'}
            </p>
          </div>
          <div className="emp-leaves__actions">
            <div className="emp-leaves__admin">
              <Button
                type="button"
                variant="secondary"
                onClick={() => setAdminOpen((open) => !open)}
                aria-expanded={adminOpen}
              >
                Manage
              </Button>
              {adminOpen ? (
                <div className="emp-leaves__admin-menu">
                  <button
                    type="button"
                    onClick={() => {
                      setAdminOpen(false);
                      setAllocError(null);
                      setAllocQuantity('1');
                      setAllocRemarks('');
                      setAllocateOpen(true);
                    }}
                  >
                    Allocate days
                  </button>
                  <button type="button" onClick={() => void handleSeed()} disabled={actionLoading}>
                    Seed from policy
                  </button>
                  <Link to="/app/setup/leave-policies" onClick={() => setAdminOpen(false)}>
                    Leave policies
                  </Link>
                </div>
              ) : null}
            </div>
            <Button type="button" onClick={openApply}>
              Apply leave
            </Button>
          </div>
        </header>

        {error ? <p className="emp-leaves__banner emp-leaves__banner--error">{error}</p> : null}

        <nav className="emp-leaves__tabs" aria-label="Leave sections">
          <button
            type="button"
            className={tab === 'overview' ? 'is-active' : ''}
            onClick={() => setTab('overview')}
          >
            Balances
          </button>
          <button
            type="button"
            className={tab === 'requests' ? 'is-active' : ''}
            onClick={() => setTab('requests')}
          >
            Requests
            {pendingCount ? <span>{pendingCount}</span> : null}
          </button>
          <button
            type="button"
            className={tab === 'activity' ? 'is-active' : ''}
            onClick={() => setTab('activity')}
          >
            Activity
          </button>
        </nav>

        {tab === 'overview' ? (
          <section className="emp-leaves__panel">
            {balances.length ? (
              <div className="emp-leaves__balance-grid">
                {balances.map((row) => {
                  const usedPct = usagePercent(row);
                  return (
                    <div key={row.id} className="emp-leaves__balance-card">
                      <div className="emp-leaves__balance-top">
                        <strong>{row.leave_type_name || 'Leave type'}</strong>
                        <span>{formatDays(row.balance)} left</span>
                      </div>
                      <div className="emp-leaves__balance-main">{formatDays(row.balance)}</div>
                      <div className="emp-leaves__meter" aria-hidden>
                        <div style={{ width: `${usedPct}%` }} />
                      </div>
                      <div className="emp-leaves__balance-meta">
                        <span>Used {formatDays(row.used)}</span>
                        <span>of {formatDays(row.allocated)}</span>
                      </div>
                    </div>
                  );
                })}
              </div>
            ) : (
              <div className="emp-leaves__empty-block">
                <strong>No balances yet</strong>
                <p>
                  Seed credits the opening amount: full annual leave for upfront policies, or
                  this month’s accrual for monthly policies.
                </p>
                <div className="emp-leaves__empty-actions">
                  <Button type="button" variant="secondary" onClick={() => void handleSeed()} disabled={actionLoading}>
                    Seed from policy
                  </Button>
                  <Button
                    type="button"
                    onClick={() => {
                      setAllocError(null);
                      setAllocateOpen(true);
                    }}
                  >
                    Allocate days
                  </Button>
                </div>
              </div>
            )}

            {pendingCount ? (
              <button
                type="button"
                className="emp-leaves__pending-callout"
                onClick={() => {
                  setRequestFilter('pending');
                  setTab('requests');
                }}
              >
                <strong>{pendingCount} pending request{pendingCount === 1 ? '' : 's'}</strong>
                <span>Review and approve</span>
              </button>
            ) : null}
          </section>
        ) : null}

        {tab === 'requests' ? (
          <section className="emp-leaves__panel">
            <div className="emp-leaves__filters">
              {(
                [
                  ['all', 'All'],
                  ['pending', 'Pending'],
                  ['decided', 'Decided'],
                ] as const
              ).map(([value, label]) => (
                <button
                  key={value}
                  type="button"
                  className={requestFilter === value ? 'is-active' : ''}
                  onClick={() => setRequestFilter(value)}
                >
                  {label}
                </button>
              ))}
            </div>

            {filteredApplications.length ? (
              <ul className="emp-leaves__list">
                {filteredApplications.map((row) => (
                  <li key={row.id} className="emp-leaves__item">
                    <div className="emp-leaves__item-main">
                      <div className="emp-leaves__item-title">
                        <strong>{row.leave_type_name}</strong>
                        <span className={`emp-leaves__status ${statusClass(row.status)}`}>
                          {STATUS_LABELS[row.status] || row.status}
                        </span>
                      </div>
                      <div className="emp-leaves__meta">
                        <span>{formatDateRange(row.from_date, row.to_date)}</span>
                        <span>{dayLabel(row.number_of_days)}{row.is_half_day ? ' · half day' : ''}</span>
                        {row.status === 'pending' && row.expected_approver_name ? (
                          <span>Approver: {row.expected_approver_name}</span>
                        ) : null}
                        {row.approved_by_name ? <span>By {row.approved_by_name}</span> : null}
                      </div>
                      <p className="emp-leaves__reason">{row.reason}</p>
                      {row.remarks ? <p className="emp-leaves__remarks">{row.remarks}</p> : null}
                    </div>
                    <div className="emp-leaves__item-side">
                      {row.status === 'pending' && row.can_review ? (
                        <div className="emp-leaves__item-actions">
                          <Button
                            type="button"
                            disabled={actionLoading}
                            onClick={() => void handleReview(row.id, true)}
                          >
                            Approve
                          </Button>
                          <Button
                            type="button"
                            variant="secondary"
                            disabled={actionLoading}
                            onClick={() => void handleReview(row.id, false)}
                          >
                            Reject
                          </Button>
                        </div>
                      ) : null}
                      {row.status === 'pending' && !row.can_review ? (
                        <span className="emp-leaves__awaiting">
                          Waiting for {row.expected_approver_name || 'manager'}
                        </span>
                      ) : null}
                      {row.status === 'pending' || row.status === 'approved' ? (
                        <Button
                          type="button"
                          variant="ghost"
                          disabled={actionLoading}
                          onClick={() => void handleCancel(row.id)}
                        >
                          Cancel
                        </Button>
                      ) : null}
                    </div>
                  </li>
                ))}
              </ul>
            ) : (
              <div className="emp-leaves__empty-block">
                <strong>No requests here</strong>
                <p>
                  {requestFilter === 'pending'
                    ? 'Nothing waiting for review.'
                    : 'Apply leave when this employee needs time off.'}
                </p>
                <Button type="button" onClick={openApply}>
                  Apply leave
                </Button>
              </div>
            )}
          </section>
        ) : null}

        {tab === 'activity' ? (
          <section className="emp-leaves__panel">
            {logs.length ? (
              <ul className="emp-leaves__log-list">
                {logs.slice(0, 20).map((row) => {
                  const qty = Number(row.quantity) || 0;
                  const signed = qty > 0 ? `+${formatDays(qty)}` : formatDays(qty);
                  return (
                    <li key={row.id}>
                      <div>
                        <strong>
                          {LOG_LABELS[row.transaction_type] || row.transaction_type}
                          {' · '}
                          {row.leave_type_name}
                        </strong>
                        <span>
                          {formatDays(row.balance_before)} → {formatDays(row.balance_after)}
                        </span>
                      </div>
                      <div className="emp-leaves__log-side">
                        <b className={qty < 0 ? 'is-down' : 'is-up'}>{signed}</b>
                        <em>{new Date(row.created_at).toLocaleString()}</em>
                      </div>
                    </li>
                  );
                })}
              </ul>
            ) : (
              <div className="emp-leaves__empty-block">
                <strong>No activity yet</strong>
                <p>Allocations, approvals, and adjustments will show up here.</p>
              </div>
            )}
          </section>
        ) : null}
      </article>

      <Modal
        open={applyOpen}
        title="Apply leave"
        onClose={() => setApplyOpen(false)}
        footer={
          <>
            <Button type="button" variant="ghost" onClick={() => setApplyOpen(false)}>
              Cancel
            </Button>
            <Button type="submit" form="leave-apply-form" loading={actionLoading}>
              Submit request
            </Button>
          </>
        }
      >
        <form id="leave-apply-form" className="emp-leaves__form" onSubmit={handleApply}>
          {applyError ? (
            <p className="emp-leaves__banner emp-leaves__banner--error">{applyError}</p>
          ) : null}

          <label className="emp-leaves__field">
            <span>Leave type</span>
            <select value={leaveTypeId} onChange={(event) => setLeaveTypeId(event.target.value)}>
              {leaveTypes.map((item) => (
                <option key={item.id} value={item.id}>
                  {item.name}
                </option>
              ))}
            </select>
          </label>

          <div className="emp-leaves__form-grid">
            <label className="emp-leaves__field">
              <span>From</span>
              <input
                type="date"
                value={fromDate}
                onChange={(event) => {
                  setFromDate(event.target.value);
                  if (isHalfDay) setToDate(event.target.value);
                }}
              />
            </label>
            <label className="emp-leaves__field">
              <span>To</span>
              <input
                type="date"
                value={toDate}
                disabled={isHalfDay}
                onChange={(event) => setToDate(event.target.value)}
              />
            </label>
          </div>

          <label className="emp-leaves__check">
            <input
              type="checkbox"
              checked={isHalfDay}
              onChange={(event) => {
                setIsHalfDay(event.target.checked);
                if (event.target.checked) setToDate(fromDate);
              }}
            />
            <span>Half day</span>
          </label>

          <div className="emp-leaves__preview">
            <span>Requesting</span>
            <strong>{dayLabel(requestedDays)}</strong>
            {selectedBalance ? (
              <em>{formatDays(selectedBalance.balance)} available in this type</em>
            ) : (
              <em>No balance for this type yet</em>
            )}
          </div>

          <label className="emp-leaves__field">
            <span>Reason</span>
            <textarea
              value={reason}
              onChange={(event) => setReason(event.target.value)}
              rows={3}
              placeholder="Why is this leave needed?"
            />
          </label>
          <label className="emp-leaves__field">
            <span>Attachment <small>optional</small></span>
            <input
              type="file"
              onChange={(event) => setAttachment(event.target.files?.[0] || null)}
            />
          </label>
        </form>
      </Modal>

      <Modal
        open={allocateOpen}
        title="Allocate leave"
        onClose={() => setAllocateOpen(false)}
        footer={
          <>
            <Button type="button" variant="ghost" onClick={() => setAllocateOpen(false)}>
              Cancel
            </Button>
            <Button type="submit" form="leave-allocate-form" loading={actionLoading}>
              Allocate
            </Button>
          </>
        }
      >
        <form id="leave-allocate-form" className="emp-leaves__form" onSubmit={handleAllocate}>
          {allocError ? (
            <p className="emp-leaves__banner emp-leaves__banner--error">{allocError}</p>
          ) : null}
          <p className="emp-leaves__modal-lead">
            Manually credit days when policy seeding is not enough.
          </p>
          <label className="emp-leaves__field">
            <span>Leave type</span>
            <select
              value={allocLeaveTypeId}
              onChange={(event) => setAllocLeaveTypeId(event.target.value)}
            >
              {leaveTypes.map((item) => (
                <option key={item.id} value={item.id}>
                  {item.name}
                </option>
              ))}
            </select>
          </label>
          <label className="emp-leaves__field">
            <span>Days to add</span>
            <input
              type="number"
              min="0.5"
              step="0.5"
              value={allocQuantity}
              onChange={(event) => setAllocQuantity(event.target.value)}
            />
          </label>
          <label className="emp-leaves__field">
            <span>Remarks <small>optional</small></span>
            <textarea
              value={allocRemarks}
              onChange={(event) => setAllocRemarks(event.target.value)}
              rows={2}
              placeholder="Why are these days being added?"
            />
          </label>
        </form>
      </Modal>
    </>
  );
}
