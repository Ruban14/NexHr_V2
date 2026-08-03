import { useCallback, useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { organizationApi } from '../../api/auth';
import { extractErrorMessage } from '../../api/client';
import { tokenStorage } from '../../auth/tokenStorage';
import { Button } from '../../components/Button';
import { DataTable, type DataTableColumn } from '../../components/ui/DataTable';
import { EmptyState } from '../../components/ui/EmptyState';
import { IconAction, IconView } from '../../components/ui/IconAction';
import { LoadingSkeleton } from '../../components/ui/LoadingSkeleton';
import { Modal } from '../../components/ui/Modal';
import { PageHeader } from '../../components/ui/PageHeader';
import { SearchBar } from '../../components/ui/SearchBar';
import { Toolbar } from '../../components/ui/Toolbar';
import type { AttendanceRecord, AttendanceSession } from '../../types';
import { useWorkspace } from '../../workspace/WorkspaceContext';
import './AttendancePage.css';

type StatusFilter = 'all' | 'present' | 'absent' | 'half_day' | 'leave' | 'holiday' | 'week_off';

const STATUS_LABELS: Record<string, string> = {
  present: 'Present',
  absent: 'Absent',
  half_day: 'Half day',
  leave: 'Leave',
  holiday: 'Holiday',
  week_off: 'Week off',
};

const APPROVAL_LABELS: Record<string, string> = {
  pending: 'Pending',
  approved: 'Approved',
  rejected: 'Rejected',
};

const SOURCE_LABELS: Record<string, string> = {
  web: 'Web',
  mobile: 'Mobile',
  biometric: 'Biometric',
  rfid: 'RFID',
  manual: 'Manual',
  api: 'API',
};

const FILTERS: { value: StatusFilter; label: string }[] = [
  { value: 'all', label: 'All' },
  { value: 'present', label: 'Present' },
  { value: 'absent', label: 'Absent' },
  { value: 'half_day', label: 'Half day' },
  { value: 'leave', label: 'Leave' },
  { value: 'holiday', label: 'Holiday' },
  { value: 'week_off', label: 'Week off' },
];

function todayIso(): string {
  const now = new Date();
  const y = now.getFullYear();
  const m = String(now.getMonth() + 1).padStart(2, '0');
  const d = String(now.getDate()).padStart(2, '0');
  return `${y}-${m}-${d}`;
}

function statusClass(status?: string | null): string {
  if (status === 'present') return 'is-ok';
  if (status === 'half_day') return 'is-warn';
  if (status === 'absent') return 'is-bad';
  if (status === 'leave' || status === 'holiday' || status === 'week_off') return 'is-muted';
  return 'is-muted';
}

function approvalClass(status?: string | null): string {
  if (status === 'approved') return 'is-ok';
  if (status === 'pending') return 'is-warn';
  if (status === 'rejected') return 'is-bad';
  return 'is-muted';
}

function nameInitials(name?: string | null, code?: string | null): string {
  const parts = (name || '').trim().split(/\s+/).filter(Boolean);
  if (parts.length >= 2) return `${parts[0][0]}${parts[1][0]}`.toUpperCase();
  if (parts.length === 1 && parts[0].length >= 2) return parts[0].slice(0, 2).toUpperCase();
  const fromCode = (code || '').replace(/[^A-Za-z0-9]/g, '');
  if (fromCode.length >= 2) return fromCode.slice(0, 2).toUpperCase();
  return 'EM';
}

function formatTime(value?: string | null): string {
  if (!value) return '—';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit' });
}

function formatHours(value?: string | null | number): string {
  if (value == null || value === '') return '—';
  const num = Number(value);
  if (Number.isNaN(num)) return String(value);
  return `${num.toFixed(2)} h`;
}

function formatDateLabel(value?: string | null): string {
  if (!value) return '—';
  const date = new Date(`${value}T00:00:00`);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleDateString(undefined, {
    weekday: 'short',
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  });
}

function formatClock(now: Date): string {
  return now.toLocaleTimeString(undefined, {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  });
}

function punchTone(openSession: boolean, onBreak: boolean): 'idle' | 'active' | 'break' {
  if (!openSession) return 'idle';
  if (onBreak) return 'break';
  return 'active';
}

function punchLabel(openSession: boolean, onBreak: boolean): string {
  if (!openSession) return 'Not checked in';
  if (onBreak) return 'On break';
  return 'Working';
}

export function AttendancePage() {
  const { currentBranch } = useWorkspace();
  const [date, setDate] = useState(todayIso);
  const [filter, setFilter] = useState<StatusFilter>('all');
  const [search, setSearch] = useState('');
  const [items, setItems] = useState<AttendanceRecord[]>([]);
  const [presentCount, setPresentCount] = useState(0);
  const [totalCount, setTotalCount] = useState(0);
  const [today, setToday] = useState<AttendanceRecord | null>(null);
  const [mySessions, setMySessions] = useState<AttendanceSession[]>([]);
  const [loading, setLoading] = useState(true);
  const [punchBusy, setPunchBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [detailRow, setDetailRow] = useState<AttendanceRecord | null>(null);
  const [now, setNow] = useState(() => new Date());

  const load = useCallback(async () => {
    const token = tokenStorage.getAccessToken();
    if (!token) return;
    setLoading(true);
    setError(null);
    try {
      const [list, mine] = await Promise.all([
        organizationApi.listAttendance(token, {
          date,
          status: filter === 'all' ? undefined : filter,
        }),
        organizationApi.getTodayAttendance(token).catch(() => null),
      ]);
      setItems(list.items);
      setPresentCount(list.present_count);
      setTotalCount(list.total_count);
      setToday(mine);
      if (mine?.employee_id) {
        const day = mine.attendance_date || todayIso();
        const sessions = await organizationApi
          .listEmployeeAttendanceSessions(token, mine.employee_id, {
            date_from: day,
            date_to: day,
          })
          .catch(() => []);
        setMySessions(sessions);
      } else {
        setMySessions([]);
      }
    } catch (err) {
      setError(extractErrorMessage(err, 'Unable to load attendance.'));
      setItems([]);
      setPresentCount(0);
      setTotalCount(0);
    } finally {
      setLoading(false);
    }
  }, [date, filter]);

  useEffect(() => {
    void load();
  }, [load, currentBranch?.branch_id]);

  useEffect(() => {
    if (!success) return;
    const timer = window.setTimeout(() => setSuccess(null), 3000);
    return () => window.clearTimeout(timer);
  }, [success]);

  useEffect(() => {
    const timer = window.setInterval(() => setNow(new Date()), 1000);
    return () => window.clearInterval(timer);
  }, []);

  const visibleItems = useMemo(() => {
    const query = search.trim().toLowerCase();
    if (!query) return items;
    return items.filter((row) => {
      const haystack = [
        row.employee_name,
        row.employee_code,
        row.employee_designation_name,
        row.remarks,
        row.status,
      ]
        .filter(Boolean)
        .join(' ')
        .toLowerCase();
      return haystack.includes(query);
    });
  }, [items, search]);

  async function punch(action: 'check-in' | 'check-out' | 'break-start' | 'break-end') {
    const token = tokenStorage.getAccessToken();
    if (!token) return;
    setPunchBusy(true);
    setError(null);
    try {
      let result: AttendanceRecord;
      if (action === 'check-in') result = await organizationApi.attendanceCheckIn(token);
      else if (action === 'check-out') result = await organizationApi.attendanceCheckOut(token);
      else if (action === 'break-start') result = await organizationApi.attendanceBreakStart(token);
      else result = await organizationApi.attendanceBreakEnd(token);
      setToday(result);
      setSuccess(
        action === 'check-in'
          ? 'Checked in.'
          : action === 'check-out'
            ? 'Checked out.'
            : action === 'break-start'
              ? 'Break started.'
              : 'Break ended.',
      );
      await load();
    } catch (err) {
      setError(extractErrorMessage(err, 'Unable to update attendance.'));
    } finally {
      setPunchBusy(false);
    }
  }

  const columns = useMemo<DataTableColumn<AttendanceRecord>[]>(
    () => [
      {
        key: 'employee_id',
        header: 'Employee ID',
        width: '110px',
        render: (row) => <span className="attendance__id">{row.employee_code || '—'}</span>,
      },
      {
        key: 'employee',
        header: 'Employee',
        width: '240px',
        render: (row) => (
          <div className="attendance__person">
            <span className="attendance__avatar" aria-hidden>
              {nameInitials(row.employee_name, row.employee_code)}
            </span>
            <div className="attendance__person-text">
              <Link className="attendance__employee" to={`/app/employees/${row.employee_id}`}>
                {row.employee_name || 'Employee'}
              </Link>
              <span className="attendance__title">{row.employee_designation_name || '—'}</span>
            </div>
          </div>
        ),
      },
      {
        key: 'check_in',
        header: 'Check in',
        width: '100px',
        render: (row) => <span className="attendance__time">{formatTime(row.first_check_in)}</span>,
      },
      {
        key: 'check_out',
        header: 'Check out',
        width: '100px',
        render: (row) => <span className="attendance__time">{formatTime(row.last_check_out)}</span>,
      },
      {
        key: 'worked',
        header: 'Worked',
        width: '90px',
        render: (row) => <span className="attendance__hours">{formatHours(row.total_worked_hours)}</span>,
      },
      {
        key: 'break',
        header: 'Break',
        width: '90px',
        render: (row) => <span className="attendance__hours">{formatHours(row.total_break_hours)}</span>,
      },
      {
        key: 'status',
        header: 'Status',
        width: '150px',
        render: (row) => (
          <div className="attendance__status-stack">
            <span className={`attendance__status ${statusClass(row.status)}`}>
              {STATUS_LABELS[row.status || ''] || row.status || '—'}
            </span>
            {row.approval_status && row.approval_status !== 'not_required' ? (
              <span className={`attendance__status ${approvalClass(row.approval_status)}`}>
                {APPROVAL_LABELS[row.approval_status] || row.approval_status}
              </span>
            ) : null}
          </div>
        ),
      },
      {
        key: 'actions',
        header: '',
        width: '64px',
        render: (row) => (
          <IconAction label="View detail" onClick={() => setDetailRow(row)}>
            <IconView />
          </IconAction>
        ),
      },
    ],
    [],
  );

  const openSession = Boolean(today?.has_open_session);
  const onBreak = Boolean(today?.on_break);
  const tone = punchTone(openSession, onBreak);
  const todayKey = today?.attendance_date || todayIso();
  const todaySessions = useMemo(() => {
    const rows = mySessions.length
      ? mySessions
      : (today?.sessions || []).map((session) => ({
          ...session,
          attendance_date: session.attendance_date || today?.attendance_date || todayKey,
        }));
    return rows
      .filter((session) => {
        const sessionDate = session.attendance_date || session.check_in?.slice(0, 10) || '';
        return sessionDate === todayKey;
      })
      .sort((left, right) => (left.check_in || '').localeCompare(right.check_in || ''));
  }, [mySessions, today, todayKey]);
  const todayWorkedHours = useMemo(
    () => todaySessions.reduce((sum, row) => sum + (Number(row.worked_hours) || 0), 0),
    [todaySessions],
  );
  const isViewingToday = date === todayIso();

  return (
    <section className="attendance">
      <PageHeader
        title="Attendance"
        description="Punch your day and review your attendance history."
        actions={
          <>
            <Link to="/app/attendance-approvals" className="attendance__approvals-link">
              Approvals
            </Link>
            {presentCount ? (
              <span className="attendance__present-pill">{presentCount} present</span>
            ) : null}
          </>
        }
      />

      <div className="attendance__me">
        <article className={`attendance__punch attendance__punch--${tone}`}>
          <div className="attendance__punch-top">
            <div className="attendance__punch-copy">
              <span className="attendance__live" data-tone={tone}>
                <i aria-hidden />
                {punchLabel(openSession, onBreak)}
              </span>
              <h2>My day</h2>
              <p>{formatDateLabel(today?.attendance_date || todayIso())}</p>
            </div>
            <div className="attendance__clock" aria-live="polite">
              <span>Local time</span>
              <strong>{formatClock(now)}</strong>
            </div>
          </div>

          {today?.approval_status === 'pending' ? (
            <p className="attendance__pending-note">
              Manual entry waiting for {today.expected_approver_name || 'manager'} approval.
            </p>
          ) : null}

          <div className="attendance__today-stats">
            <div>
              <span>Check in</span>
              <strong>{formatTime(today?.first_check_in)}</strong>
            </div>
            <div>
              <span>Check out</span>
              <strong>{formatTime(today?.last_check_out)}</strong>
            </div>
            <div>
              <span>Worked</span>
              <strong>{formatHours(today?.total_worked_hours)}</strong>
            </div>
            <div>
              <span>Break</span>
              <strong>{formatHours(today?.total_break_hours)}</strong>
            </div>
          </div>

          <div className="attendance__today-actions">
            {!openSession ? (
              <Button type="button" loading={punchBusy} onClick={() => void punch('check-in')}>
                Check in
              </Button>
            ) : (
              <>
                {onBreak ? (
                  <Button
                    type="button"
                    variant="secondary"
                    loading={punchBusy}
                    onClick={() => void punch('break-end')}
                  >
                    End break
                  </Button>
                ) : (
                  <Button
                    type="button"
                    variant="secondary"
                    loading={punchBusy}
                    onClick={() => void punch('break-start')}
                  >
                    Start break
                  </Button>
                )}
                <Button
                  type="button"
                  loading={punchBusy}
                  disabled={onBreak}
                  onClick={() => void punch('check-out')}
                >
                  Check out
                </Button>
              </>
            )}
          </div>
        </article>

        <article className="attendance__my-sessions">
          <header>
            <div>
              <h3>Today’s sessions</h3>
              <p>{formatDateLabel(todayKey)}</p>
            </div>
            {todaySessions.length ? (
              <span className="attendance__session-count">
                {todaySessions.length} session{todaySessions.length === 1 ? '' : 's'}
                {todayWorkedHours > 0 ? ` · ${formatHours(todayWorkedHours)}` : ''}
              </span>
            ) : null}
          </header>

          {todaySessions.length ? (
            <ul className="attendance__today-session-list">
              {todaySessions.map((session) => (
                <li key={session.id}>
                  <div className="attendance__session-rail" aria-hidden />
                  <div className="attendance__session-body">
                    <strong>
                      {formatTime(session.check_in)} – {formatTime(session.check_out)}
                    </strong>
                    {session.breaks?.length ? (
                      <span>
                        Breaks:{' '}
                        {session.breaks
                          .map(
                            (item) =>
                              `${formatTime(item.break_start)}–${formatTime(item.break_end)}`,
                          )
                          .join(', ')}
                      </span>
                    ) : (
                      <span>No breaks</span>
                    )}
                  </div>
                  <div className="attendance__session-meta">
                    <span>{formatHours(session.worked_hours)}</span>
                    <em>{SOURCE_LABELS[session.source] || session.source}</em>
                    {session.approval_status && session.approval_status !== 'not_required' ? (
                      <em className={`attendance__status ${approvalClass(session.approval_status)}`}>
                        {APPROVAL_LABELS[session.approval_status] || session.approval_status}
                      </em>
                    ) : null}
                  </div>
                </li>
              ))}
            </ul>
          ) : (
            <p className="attendance__sessions-empty">
              No sessions yet today. Your check-ins will appear here after you punch in.
            </p>
          )}
        </article>
      </div>

      <section className="attendance__register">
        <header className="attendance__register-head">
          <div>
            <h3>My attendance</h3>
            <p>
              {isViewingToday ? 'Today' : formatDateLabel(date)}
              {filter === 'all' && totalCount
                ? ` · ${presentCount} present of ${totalCount}`
                : totalCount
                  ? ` · ${totalCount} record${totalCount === 1 ? '' : 's'}`
                  : ''}
            </p>
          </div>
        </header>

        <Toolbar
          left={
            <div className="attendance__toolbar">
              <label className="attendance__date-field">
                <span>Date</span>
                <input
                  type="date"
                  value={date}
                  onChange={(event) => setDate(event.target.value)}
                />
              </label>
              <div className="attendance__filters" role="tablist" aria-label="Status filter">
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
                  </button>
                ))}
              </div>
              <SearchBar
                className="attendance__search"
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

        {error ? <p className="attendance__banner attendance__banner--error">{error}</p> : null}
        {success ? (
          <p className="attendance__banner attendance__banner--success">{success}</p>
        ) : null}

        {loading ? (
          <LoadingSkeleton rows={6} />
        ) : (
          <div className="attendance__table">
            <DataTable
              columns={columns}
              rows={visibleItems}
              empty={
                <EmptyState
                  title="No attendance records"
                  description={
                    search.trim()
                      ? 'Try a different search.'
                      : 'Check-ins for this date will appear here.'
                  }
                />
              }
            />
          </div>
        )}
      </section>

      <Modal
        open={Boolean(detailRow)}
        title="Attendance detail"
        onClose={() => setDetailRow(null)}
        footer={
          <Button type="button" variant="secondary" onClick={() => setDetailRow(null)}>
            Close
          </Button>
        }
      >
        {detailRow ? (
          <div className="attendance__detail">
            <div className="attendance__detail-person">
              <span className="attendance__avatar attendance__avatar--lg" aria-hidden>
                {nameInitials(detailRow.employee_name, detailRow.employee_code)}
              </span>
              <div>
                <strong>{detailRow.employee_name || 'Employee'}</strong>
                <span>
                  {detailRow.employee_code || '—'}
                  {detailRow.employee_designation_name
                    ? ` · ${detailRow.employee_designation_name}`
                    : ''}
                </span>
              </div>
            </div>

            <dl className="attendance__detail-grid">
              <div>
                <dt>Date</dt>
                <dd>{formatDateLabel(detailRow.attendance_date)}</dd>
              </div>
              <div>
                <dt>Status</dt>
                <dd>
                  <span className={`attendance__status ${statusClass(detailRow.status)}`}>
                    {STATUS_LABELS[detailRow.status || ''] || detailRow.status || '—'}
                  </span>
                </dd>
              </div>
              <div>
                <dt>Check in</dt>
                <dd>{formatTime(detailRow.first_check_in)}</dd>
              </div>
              <div>
                <dt>Check out</dt>
                <dd>{formatTime(detailRow.last_check_out)}</dd>
              </div>
              <div>
                <dt>Worked</dt>
                <dd>{formatHours(detailRow.total_worked_hours)}</dd>
              </div>
              <div>
                <dt>Break</dt>
                <dd>{formatHours(detailRow.total_break_hours)}</dd>
              </div>
            </dl>

            {(detailRow.sessions || []).length ? (
              <ul className="attendance__sessions">
                {detailRow.sessions.map((session) => (
                  <li key={session.id}>
                    <strong>
                      {formatTime(session.check_in)} – {formatTime(session.check_out)}
                    </strong>
                    <span>
                      {formatHours(session.worked_hours)} ·{' '}
                      {SOURCE_LABELS[session.source] || session.source}
                    </span>
                    {session.breaks.length ? (
                      <em>
                        Breaks:{' '}
                        {session.breaks
                          .map(
                            (item) =>
                              `${formatTime(item.break_start)}–${formatTime(item.break_end)}`,
                          )
                          .join(', ')}
                      </em>
                    ) : null}
                  </li>
                ))}
              </ul>
            ) : (
              <p className="attendance__muted">No sessions recorded.</p>
            )}

            {detailRow.remarks ? (
              <div className="attendance__detail-reason">
                <span>Remarks</span>
                <p>{detailRow.remarks}</p>
              </div>
            ) : null}
          </div>
        ) : null}
      </Modal>
    </section>
  );
}
