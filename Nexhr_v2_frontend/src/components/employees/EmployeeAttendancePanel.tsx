import { useCallback, useEffect, useMemo, useState, type FormEvent } from 'react';
import { Link } from 'react-router-dom';
import { organizationApi } from '../../api/auth';
import { extractErrorMessage } from '../../api/client';
import { tokenStorage } from '../../auth/tokenStorage';
import type { AttendanceRecord, AttendanceSession } from '../../types';
import { useWorkspace } from '../../workspace/WorkspaceContext';
import { Button } from '../Button';
import { LoadingSkeleton } from '../ui/LoadingSkeleton';
import { Modal } from '../ui/Modal';
import './EmployeeAttendancePanel.css';

type EmployeeAttendancePanelProps = {
  employeeId: string;
};

type HistoryTab = 'sessions' | 'summary';

type SessionDateGroup = {
  date: string;
  sessions: AttendanceSession[];
  workedHours: number;
};

const STATUS_LABELS: Record<string, string> = {
  present: 'Present',
  absent: 'Absent',
  half_day: 'Half day',
  leave: 'Leave',
  holiday: 'Holiday',
  week_off: 'Week off',
};

const APPROVAL_LABELS: Record<string, string> = {
  not_required: '',
  pending: 'Pending approval',
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
  return 'is-muted';
}

function approvalClass(status?: string | null): string {
  if (status === 'approved') return 'is-ok';
  if (status === 'pending') return 'is-warn';
  if (status === 'rejected') return 'is-bad';
  return 'is-muted';
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

function formatDate(value?: string | null): string {
  if (!value) return '—';
  const date = new Date(`${value}T00:00:00`);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleDateString(undefined, {
    weekday: 'short',
    day: '2-digit',
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

function toTimeInput(value?: string | null): string {
  if (!value) return '';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return '';
  return date.toLocaleTimeString('en-GB', {
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
  });
}

function findDayRecord(
  items: AttendanceRecord[],
  today: AttendanceRecord | null,
  date: string,
): AttendanceRecord | null {
  const fromHistory = items.find((row) => row.attendance_date === date);
  if (fromHistory) return fromHistory;
  if (today?.attendance_date === date) return today;
  return null;
}

function findManualForDate(
  items: AttendanceRecord[],
  today: AttendanceRecord | null,
  date: string,
): AttendanceRecord | null {
  const day = findDayRecord(items, today, date);
  if (day?.is_manual) return day;
  return null;
}

function hasLivePunches(
  day: AttendanceRecord | null,
  sessionRows: AttendanceSession[],
  date: string,
): boolean {
  if (day?.sessions?.some((session) => session.source !== 'manual')) return true;
  return sessionRows.some(
    (session) =>
      (session.attendance_date || session.check_in?.slice(0, 10)) === date &&
      session.source !== 'manual',
  );
}

function manualSession(row: AttendanceRecord | null): AttendanceSession | null {
  if (!row?.sessions?.length) return null;
  return row.sessions.find((session) => session.source === 'manual') || row.sessions[0] || null;
}

function groupSessionsByDate(sessions: AttendanceSession[]): SessionDateGroup[] {
  const map = new Map<string, AttendanceSession[]>();
  for (const session of sessions) {
    const key = session.attendance_date || session.check_in?.slice(0, 10) || 'unknown';
    const list = map.get(key) || [];
    list.push(session);
    map.set(key, list);
  }
  return Array.from(map.entries())
    .sort(([a], [b]) => b.localeCompare(a))
    .map(([date, rows]) => {
      const ordered = [...rows].sort((left, right) =>
        (left.check_in || '').localeCompare(right.check_in || ''),
      );
      const workedHours = ordered.reduce((sum, row) => sum + (Number(row.worked_hours) || 0), 0);
      return { date, sessions: ordered, workedHours };
    });
}

export function EmployeeAttendancePanel({ employeeId }: EmployeeAttendancePanelProps) {
  const { profile } = useWorkspace();
  const isOwnProfile = Boolean(profile?.id && profile.id === employeeId);
  const [items, setItems] = useState<AttendanceRecord[]>([]);
  const [sessions, setSessions] = useState<AttendanceSession[]>([]);
  const [today, setToday] = useState<AttendanceRecord | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [historyTab, setHistoryTab] = useState<HistoryTab>('sessions');
  const [now, setNow] = useState(() => new Date());
  const [manualOpen, setManualOpen] = useState(false);
  const [manualError, setManualError] = useState<string | null>(null);
  const [manualInfo, setManualInfo] = useState<string | null>(null);
  const [manualDate, setManualDate] = useState(todayIso);
  const [manualCheckIn, setManualCheckIn] = useState('');
  const [manualCheckOut, setManualCheckOut] = useState('');
  const [manualRemarks, setManualRemarks] = useState('');
  const [manualMode, setManualMode] = useState<'create' | 'edit' | 'locked'>('create');
  const [manualDateLocked, setManualDateLocked] = useState(false);

  const applyManualDate = useCallback(
    (
      date: string,
      records: AttendanceRecord[],
      todayRecord: AttendanceRecord | null,
      sessionRows: AttendanceSession[],
    ) => {
      setManualDate(date);
      const day = findDayRecord(records, todayRecord, date);
      const existing = day?.is_manual ? day : null;
      const approval = existing?.approval_status;

      if (hasLivePunches(day, sessionRows, date)) {
        setManualMode('locked');
        setManualInfo(null);
        setManualError(
          'Check-in/check-out already exists for this date. Choose another day with no punches.',
        );
        setManualCheckIn(toTimeInput(day?.first_check_in));
        setManualCheckOut(toTimeInput(day?.last_check_out));
        setManualRemarks(day?.remarks || '');
        return;
      }

      if (existing && approval === 'approved') {
        setManualMode('locked');
        setManualInfo(null);
        setManualError(
          'Manual attendance for this date is already approved. Choose another day.',
        );
        const session = manualSession(existing);
        setManualCheckIn(toTimeInput(session?.check_in || existing.first_check_in));
        setManualCheckOut(toTimeInput(session?.check_out || existing.last_check_out));
        setManualRemarks(existing.remarks || '');
        return;
      }

      if (existing && approval === 'pending') {
        setManualMode('edit');
        setManualError(null);
        setManualInfo(
          'A request is already raised for this date. You can edit it while it is pending approval.',
        );
        const session = manualSession(existing);
        setManualCheckIn(toTimeInput(session?.check_in || existing.first_check_in));
        setManualCheckOut(toTimeInput(session?.check_out || existing.last_check_out));
        setManualRemarks(existing.remarks || '');
        return;
      }

      setManualMode('create');
      setManualError(null);
      setManualInfo(
        existing && approval === 'rejected'
          ? 'Previous request was rejected. You can submit a new request for this date.'
          : null,
      );
      setManualCheckIn('');
      setManualCheckOut('');
      setManualRemarks('');
    },
    [],
  );

  const load = useCallback(async () => {
    if (!isOwnProfile) {
      setItems([]);
      setToday(null);
      setSessions([]);
      setLoading(false);
      return;
    }
    const token = tokenStorage.getAccessToken();
    if (!token) return;
    setLoading(true);
    setError(null);
    try {
      const [history, day, sessionRows] = await Promise.all([
        organizationApi.listEmployeeAttendance(token, employeeId),
        organizationApi.getTodayAttendance(token, employeeId).catch(() => null),
        organizationApi.listEmployeeAttendanceSessions(token, employeeId),
      ]);
      setItems(history);
      setToday(day);
      setSessions(sessionRows);
    } catch (err) {
      setError(extractErrorMessage(err, 'Unable to load attendance.'));
      setItems([]);
      setToday(null);
      setSessions([]);
    } finally {
      setLoading(false);
    }
  }, [employeeId, isOwnProfile]);

  useEffect(() => {
    void load();
  }, [load]);

  useEffect(() => {
    if (!success) return;
    const timer = window.setTimeout(() => setSuccess(null), 3000);
    return () => window.clearTimeout(timer);
  }, [success]);

  useEffect(() => {
    const timer = window.setInterval(() => setNow(new Date()), 1000);
    return () => window.clearInterval(timer);
  }, []);

  async function punch(action: 'check-in' | 'check-out' | 'break-start' | 'break-end') {
    const token = tokenStorage.getAccessToken();
    if (!token) return;
    setBusy(true);
    setError(null);
    try {
      let result: AttendanceRecord;
      if (action === 'check-in') {
        result = await organizationApi.employeeAttendanceCheckIn(token, employeeId);
      } else if (action === 'check-out') {
        result = await organizationApi.employeeAttendanceCheckOut(token, employeeId);
      } else if (action === 'break-start') {
        result = await organizationApi.employeeAttendanceBreakStart(token, employeeId);
      } else {
        result = await organizationApi.employeeAttendanceBreakEnd(token, employeeId);
      }
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
      setBusy(false);
    }
  }

  async function saveManual(event: FormEvent) {
    event.preventDefault();
    const token = tokenStorage.getAccessToken();
    if (!token) return;
    if (manualMode === 'locked') {
      setManualError(manualError || 'Manual adjustment is not allowed for this date.');
      return;
    }
    if (!manualCheckIn) {
      setManualError('Check-in time is required for manual entry.');
      return;
    }
    setBusy(true);
    setManualError(null);
    try {
      const checkInIso = new Date(`${manualDate}T${manualCheckIn}:00`).toISOString();
      const checkOutIso = manualCheckOut
        ? new Date(`${manualDate}T${manualCheckOut}:00`).toISOString()
        : null;
      await organizationApi.manualEmployeeAttendance(token, employeeId, {
        attendance_date: manualDate,
        check_in: checkInIso,
        check_out: checkOutIso,
        remarks: manualRemarks,
      });
      setManualOpen(false);
      setManualError(null);
      setManualInfo(null);
      setSuccess(
        manualMode === 'edit'
          ? 'Manual entry updated. Waiting for reporting manager approval.'
          : 'Manual entry submitted for reporting manager approval.',
      );
      await load();
    } catch (err) {
      setManualError(extractErrorMessage(err, 'Unable to submit manual attendance.'));
    } finally {
      setBusy(false);
    }
  }

  function openManual(forDate?: string, lockDate = false) {
    const date = forDate || todayIso();
    applyManualDate(date, items, today, sessions);
    setManualDateLocked(lockDate);
    setManualOpen(true);
  }

  function closeManual() {
    if (busy) return;
    setManualOpen(false);
    setManualError(null);
    setManualInfo(null);
    setManualDateLocked(false);
  }

  function onManualDateChange(date: string) {
    setManualDateLocked(false);
    applyManualDate(date, items, today, sessions);
  }

  const todayKeyIso = todayIso();
  const todayManual = findManualForDate(items, today, todayKeyIso);
  const todayManualPending = todayManual?.approval_status === 'pending';
  const todayHasLivePunches = hasLivePunches(
    findDayRecord(items, today, todayKeyIso),
    sessions,
    todayKeyIso,
  );
  const openSession = Boolean(today?.has_open_session);
  const onBreak = Boolean(today?.on_break);
  const tone = punchTone(openSession, onBreak);
  const sessionGroups = useMemo(() => groupSessionsByDate(sessions), [sessions]);
  const todayKey = today?.attendance_date || todayKeyIso;
  const presentDays = useMemo(
    () => items.filter((row) => row.status === 'present').length,
    [items],
  );

  if (!isOwnProfile) {
    return (
      <div className="emp-attendance">
        <p className="emp-attendance__banner emp-attendance__banner--info">
          Attendance can only be managed from your own employee profile. Use{' '}
          <Link to="/app/attendance">Attendance</Link> for your punches.
        </p>
      </div>
    );
  }

  if (loading) return <LoadingSkeleton rows={5} />;

  return (
    <div className="emp-attendance">
      {error ? <p className="emp-attendance__banner emp-attendance__banner--error">{error}</p> : null}
      {success ? (
        <p className="emp-attendance__banner emp-attendance__banner--success">{success}</p>
      ) : null}

      <div className="emp-attendance__me">
        <article className={`emp-attendance__punch emp-attendance__punch--${tone}`}>
          <div className="emp-attendance__punch-top">
            <div className="emp-attendance__punch-copy">
              <span className="emp-attendance__live" data-tone={tone}>
                <i aria-hidden />
                {punchLabel(openSession, onBreak)}
              </span>
              <h3>My day</h3>
              <p>{formatDate(today?.attendance_date || todayIso())}</p>
            </div>
            <div className="emp-attendance__clock" aria-live="polite">
              <span>Local time</span>
              <strong>{formatClock(now)}</strong>
            </div>
          </div>

          {todayManualPending && !todayHasLivePunches ? (
            <p className="emp-attendance__pending-note">
              Manual entry waiting for{' '}
              {today?.expected_approver_name || 'reporting manager'} approval. You can edit it
              until it is approved.
            </p>
          ) : null}

          <div className="emp-attendance__stats">
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

          <div className="emp-attendance__punch-footer">
            <div className="emp-attendance__actions">
              {!openSession ? (
                <Button type="button" loading={busy} onClick={() => void punch('check-in')}>
                  Check in
                </Button>
              ) : (
                <>
                  {onBreak ? (
                    <Button
                      type="button"
                      variant="secondary"
                      loading={busy}
                      onClick={() => void punch('break-end')}
                    >
                      End break
                    </Button>
                  ) : (
                    <Button
                      type="button"
                      variant="secondary"
                      loading={busy}
                      onClick={() => void punch('break-start')}
                    >
                      Start break
                    </Button>
                  )}
                  <Button
                    type="button"
                    loading={busy}
                    disabled={onBreak}
                    onClick={() => void punch('check-out')}
                  >
                    Check out
                  </Button>
                </>
              )}
            </div>

            <div className="emp-attendance__manual-actions">
              {todayHasLivePunches ? (
                <span className="emp-attendance__manual-locked" title="Today already has punches">
                  Today punched
                </span>
              ) : null}
              <Button type="button" variant="secondary" onClick={() => openManual()}>
                Manual entry
              </Button>
            </div>
          </div>
        </article>

        <aside className="emp-attendance__glance">
          <h4>At a glance</h4>
          <ul>
            <li>
              <span>Days recorded</span>
              <strong>{items.length}</strong>
            </li>
            <li>
              <span>Present days</span>
              <strong>{presentDays}</strong>
            </li>
            <li>
              <span>Sessions</span>
              <strong>{sessions.length}</strong>
            </li>
            <li>
              <span>Today status</span>
              <strong>
                {today?.status
                  ? STATUS_LABELS[today.status] || today.status
                  : openSession
                    ? 'In progress'
                    : '—'}
              </strong>
            </li>
          </ul>
          <Link className="emp-attendance__full-link" to="/app/attendance">
            Open full attendance page
          </Link>
        </aside>
      </div>

      <section className="emp-attendance__history">
        <header className="emp-attendance__history-head">
          <div>
            <h3>History</h3>
            <p>Review punches and daily totals for recent days.</p>
          </div>
          <div className="emp-attendance__tabs" role="tablist" aria-label="Attendance history">
            <button
              type="button"
              role="tab"
              aria-selected={historyTab === 'sessions'}
              className={historyTab === 'sessions' ? 'is-active' : ''}
              onClick={() => setHistoryTab('sessions')}
            >
              Sessions
              {sessionGroups.length ? <em>{sessionGroups.length}</em> : null}
            </button>
            <button
              type="button"
              role="tab"
              aria-selected={historyTab === 'summary'}
              className={historyTab === 'summary' ? 'is-active' : ''}
              onClick={() => setHistoryTab('summary')}
            >
              Daily summary
              {items.length ? <em>{items.length}</em> : null}
            </button>
          </div>
        </header>

        {historyTab === 'sessions' ? (
          sessionGroups.length ? (
            <div className="emp-attendance__accordion">
              {sessionGroups.map((group) => (
                <details
                  key={group.date}
                  className="emp-attendance__day"
                  open={group.date === todayKey}
                >
                  <summary>
                    <span className="emp-attendance__day-main">
                      <strong>{formatDate(group.date)}</strong>
                      <em>
                        {group.sessions.length} session
                        {group.sessions.length === 1 ? '' : 's'}
                      </em>
                    </span>
                    <span className="emp-attendance__day-meta">
                      {formatHours(group.workedHours)}
                    </span>
                  </summary>
                  <ul className="emp-attendance__sessions">
                    {group.sessions.map((session) => (
                      <li key={session.id}>
                        <span className="emp-attendance__session-rail" aria-hidden />
                        <div className="emp-attendance__session-body">
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
                        <div className="emp-attendance__list-meta">
                          <span>{formatHours(session.worked_hours)}</span>
                          <em className="emp-attendance__source">
                            {SOURCE_LABELS[session.source] || session.source}
                          </em>
                          {session.approval_status && session.approval_status !== 'not_required' ? (
                            <em
                              className={`emp-attendance__status ${approvalClass(session.approval_status)}`}
                            >
                              {APPROVAL_LABELS[session.approval_status] || session.approval_status}
                            </em>
                          ) : null}
                        </div>
                      </li>
                    ))}
                  </ul>
                </details>
              ))}
            </div>
          ) : (
            <p className="emp-attendance__empty">No check-in sessions yet.</p>
          )
        ) : items.length ? (
          <ul className="emp-attendance__list">
            {items.map((row) => {
              const canEditManual =
                Boolean(row.is_manual) && row.approval_status === 'pending' && row.attendance_date;
              return (
                <li key={row.id || row.attendance_date}>
                  <div className="emp-attendance__list-main">
                    <strong>{formatDate(row.attendance_date)}</strong>
                    <span>
                      {formatTime(row.first_check_in)} – {formatTime(row.last_check_out)}
                      {row.sessions?.length ? ` · ${row.sessions.length} session(s)` : ''}
                    </span>
                  </div>
                  <div className="emp-attendance__list-meta">
                    <span className="emp-attendance__hours">
                      {formatHours(row.total_worked_hours)}
                    </span>
                    <em className={`emp-attendance__status ${statusClass(row.status)}`}>
                      {STATUS_LABELS[row.status || ''] || row.status || '—'}
                    </em>
                    {row.approval_status && row.approval_status !== 'not_required' ? (
                      <em
                        className={`emp-attendance__status ${approvalClass(row.approval_status)}`}
                      >
                        {APPROVAL_LABELS[row.approval_status] || row.approval_status}
                      </em>
                    ) : null}
                    {canEditManual ? (
                      <Button
                        type="button"
                        variant="ghost"
                        onClick={() => openManual(row.attendance_date || undefined, true)}
                      >
                        Edit
                      </Button>
                    ) : null}
                  </div>
                </li>
              );
            })}
          </ul>
        ) : (
          <p className="emp-attendance__empty">No attendance records yet.</p>
        )}
      </section>

      <Modal
        open={manualOpen}
        title={manualMode === 'edit' ? 'Edit manual attendance' : 'Manual attendance'}
        onClose={closeManual}
        footer={
          <>
            <Button type="button" variant="ghost" disabled={busy} onClick={closeManual}>
              Cancel
            </Button>
            {manualMode !== 'locked' ? (
              <Button type="submit" form="emp-attendance-manual" loading={busy}>
                {manualMode === 'edit' ? 'Update request' : 'Submit for approval'}
              </Button>
            ) : null}
          </>
        }
      >
        <form id="emp-attendance-manual" className="emp-attendance__manual" onSubmit={saveManual}>
          <p className="emp-attendance__manual-hint">
            Pick any day without check-in/check-out. If today is already punched, choose yesterday
            or another open day. Pending requests can be edited; approved requests cannot.
          </p>
          {manualInfo ? (
            <p className="emp-attendance__banner emp-attendance__banner--info">{manualInfo}</p>
          ) : null}
          {manualError ? (
            <p className="emp-attendance__banner emp-attendance__banner--error">{manualError}</p>
          ) : null}
          <label>
            <span>Date</span>
            <input
              type="date"
              required
              value={manualDate}
              max={todayIso()}
              disabled={manualDateLocked}
              onChange={(event) => onManualDateChange(event.target.value)}
            />
          </label>
          <label>
            <span>Check in</span>
            <input
              type="time"
              required
              value={manualCheckIn}
              disabled={manualMode === 'locked'}
              onChange={(event) => setManualCheckIn(event.target.value)}
            />
          </label>
          <label>
            <span>Check out</span>
            <input
              type="time"
              value={manualCheckOut}
              disabled={manualMode === 'locked'}
              onChange={(event) => setManualCheckOut(event.target.value)}
            />
          </label>
          <label className="emp-attendance__manual-full">
            <span>Remarks</span>
            <textarea
              rows={2}
              value={manualRemarks}
              disabled={manualMode === 'locked'}
              onChange={(event) => setManualRemarks(event.target.value)}
              placeholder="Why this manual entry is needed"
            />
          </label>
        </form>
      </Modal>
    </div>
  );
}
