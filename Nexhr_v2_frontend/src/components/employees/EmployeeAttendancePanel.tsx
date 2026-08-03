import { useCallback, useEffect, useMemo, useState, type FormEvent } from 'react';
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

type SessionDateGroup = {
  date: string;
  sessions: AttendanceSession[];
  workedHours: number;
};

type DayHistoryRow = {
  date: string;
  record: AttendanceRecord | null;
  sessions: AttendanceSession[];
  workedHours: string | number | null;
  hasLive: boolean;
  hasManual: boolean;
  isLogoutOnlyManual: boolean;
  hasOpenLogout: boolean;
  entryLabel: string;
  approvalLabel: string | null;
  notice: string | null;
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

function sessionsForDate(
  day: AttendanceRecord | null,
  sessionRows: AttendanceSession[],
  date: string,
): AttendanceSession[] {
  if (day?.sessions?.length) return day.sessions;
  return sessionRows.filter(
    (session) => (session.attendance_date || session.check_in?.slice(0, 10)) === date,
  );
}

function hasMissingLogout(
  day: AttendanceRecord | null,
  sessionRows: AttendanceSession[],
  date: string,
  today: string,
): boolean {
  if (!date || date >= today) return false;
  const rows = sessionsForDate(day, sessionRows, date);
  const live = rows.filter((session) => session.source !== 'manual');
  if (!live.length) return false;
  if (live.some((session) => !session.check_out)) return true;
  return Boolean(day?.is_manual && day.approval_status === 'pending');
}

function openLiveSession(
  day: AttendanceRecord | null,
  sessionRows: AttendanceSession[],
  date: string,
): AttendanceSession | null {
  const rows = sessionsForDate(day, sessionRows, date);
  return (
    rows.find((session) => session.source !== 'manual' && !session.check_out) ||
    rows.find((session) => session.source !== 'manual') ||
    null
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

function buildDayHistoryRows(
  records: AttendanceRecord[],
  todayRecord: AttendanceRecord | null,
  sessionRows: AttendanceSession[],
  today: string,
): DayHistoryRow[] {
  const byDate = new Map<string, { record: AttendanceRecord | null; sessions: AttendanceSession[] }>();

  const upsert = (date: string, record: AttendanceRecord | null, extra: AttendanceSession[] = []) => {
    const current = byDate.get(date) || { record: null, sessions: [] };
    const mergedSessions = [...current.sessions];
    const seen = new Set(mergedSessions.map((item) => item.id));
    for (const session of extra) {
      if (!seen.has(session.id)) {
        mergedSessions.push(session);
        seen.add(session.id);
      }
    }
    byDate.set(date, {
      record: record || current.record,
      sessions: mergedSessions.sort((left, right) =>
        (left.check_in || '').localeCompare(right.check_in || ''),
      ),
    });
  };

  for (const row of records) {
    if (!row.attendance_date) continue;
    upsert(row.attendance_date, row, row.sessions || []);
  }
  if (todayRecord?.attendance_date) {
    upsert(todayRecord.attendance_date, todayRecord, todayRecord.sessions || []);
  }
  for (const group of groupSessionsByDate(sessionRows)) {
    upsert(group.date, null, group.sessions);
  }

  return Array.from(byDate.entries())
    .sort(([a], [b]) => b.localeCompare(a))
    .map(([date, value]) => {
      const live = value.sessions.filter((session) => session.source !== 'manual');
      const manual = value.sessions.filter((session) => session.source === 'manual');
      const hasLive = live.length > 0;
      const hasManual = Boolean(value.record?.is_manual) || manual.length > 0;
      const isLogoutOnlyManual = hasLive && Boolean(value.record?.is_manual);
      const hasOpenLogout =
        date < today && live.some((session) => !session.check_out || session.is_open);

      let entryLabel = 'No punches';
      if (isLogoutOnlyManual) entryLabel = 'Check-in + manual logout';
      else if (hasManual && !hasLive) entryLabel = 'Manual entry';
      else if (hasLive) entryLabel = 'Check-in / check-out';

      let approvalLabel: string | null = null;
      if (hasManual && value.record?.approval_status && value.record.approval_status !== 'not_required') {
        approvalLabel = APPROVAL_LABELS[value.record.approval_status] || value.record.approval_status;
      }

      let notice: string | null = null;
      if (hasOpenLogout) {
        notice = 'No logout — still logged in';
      } else if (date === today && value.record?.has_open_session) {
        notice = 'Session open';
      }

      const workedHours =
        value.record?.total_worked_hours ??
        live.concat(manual).reduce((sum, row) => sum + (Number(row.worked_hours) || 0), 0);

      return {
        date,
        record: value.record,
        sessions: value.sessions,
        workedHours,
        hasLive,
        hasManual,
        isLogoutOnlyManual,
        hasOpenLogout,
        entryLabel,
        approvalLabel,
        notice,
      };
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
  const [detailDay, setDetailDay] = useState<DayHistoryRow | null>(null);
  const [now, setNow] = useState(() => new Date());
  const [manualOpen, setManualOpen] = useState(false);
  const [manualError, setManualError] = useState<string | null>(null);
  const [manualInfo, setManualInfo] = useState<string | null>(null);
  const [manualDate, setManualDate] = useState(todayIso);
  const [manualCheckIn, setManualCheckIn] = useState('');
  const [manualCheckOut, setManualCheckOut] = useState('');
  const [manualRemarks, setManualRemarks] = useState('');
  const [manualMode, setManualMode] = useState<'create' | 'edit' | 'checkout_adjust' | 'locked'>(
    'create',
  );
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
      const today = todayIso();
      const missingLogout = hasMissingLogout(day, sessionRows, date, today);

      if (missingLogout) {
        const live = openLiveSession(day, sessionRows, date);
        const pending = approval === 'pending';
        setManualMode(pending ? 'edit' : 'checkout_adjust');
        setManualError(null);
        setManualInfo(
          pending
            ? 'Missing logout adjustment is waiting for reporting manager approval. You can update the check-out time.'
            : 'This day has check-in but no logout. Set the missing check-out; it will need reporting manager approval.',
        );
        setManualCheckIn(toTimeInput(live?.check_in || day?.first_check_in));
        setManualCheckOut(toTimeInput(live?.check_out || day?.last_check_out));
        setManualRemarks(day?.remarks || '');
        return;
      }

      if (hasLivePunches(day, sessionRows, date)) {
        setManualMode('locked');
        setManualInfo(null);
        setManualError(
          'Check-in/check-out already exists for this date. Only a missing logout from a previous day can be adjusted.',
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
    if (
      today?.is_manual &&
      (today.approval_status === 'pending' || today.approval_status === 'approved')
    ) {
      setError(
        'This day already has a manual attendance entry. Check-in and check-out are not allowed.',
      );
      return;
    }
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
    if (!manualCheckOut) {
      setManualError('Check-out time is required for manual entry.');
      return;
    }
    if (!manualRemarks.trim()) {
      setManualError('Remarks are required for manual entry.');
      return;
    }
    const adjustingLogout =
      manualMode === 'checkout_adjust' ||
      hasMissingLogout(findDayRecord(items, today, manualDate), sessions, manualDate, todayIso());
    setBusy(true);
    setManualError(null);
    try {
      const checkInIso = new Date(`${manualDate}T${manualCheckIn}:00`).toISOString();
      const checkOutIso = new Date(`${manualDate}T${manualCheckOut}:00`).toISOString();
      await organizationApi.manualEmployeeAttendance(token, employeeId, {
        attendance_date: manualDate,
        check_in: checkInIso,
        check_out: checkOutIso,
        remarks: manualRemarks.trim(),
      });
      setManualOpen(false);
      setManualError(null);
      setManualInfo(null);
      setSuccess(
        adjustingLogout
          ? 'Missing logout submitted for reporting manager approval.'
          : manualMode === 'edit'
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
  const adjustingLogout =
    manualMode === 'checkout_adjust' ||
    (manualOpen &&
      hasMissingLogout(findDayRecord(items, today, manualDate), sessions, manualDate, todayKeyIso));
  const openSession = Boolean(today?.has_open_session);
  const onBreak = Boolean(today?.on_break);
  const tone = punchTone(openSession, onBreak);
  const historyRows = useMemo(
    () => buildDayHistoryRows(items, today, sessions, todayKeyIso),
    [items, today, sessions, todayKeyIso],
  );

  const punchesLocked = Boolean(
    today?.is_manual &&
      (today.approval_status === 'pending' || today.approval_status === 'approved'),
  );
  const presentDays = useMemo(
    () => items.filter((row) => row.status === 'present').length,
    [items],
  );
  const pendingCount = useMemo(
    () => items.filter((row) => row.is_manual && row.approval_status === 'pending').length,
    [items],
  );

  if (!isOwnProfile) {
    return (
      <div className="emp-attendance">
        <p className="emp-attendance__banner emp-attendance__banner--info">
          Attendance can only be managed from your own employee profile.
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

          {punchesLocked ? (
            <p className="emp-attendance__pending-note">
              Manual entry is on record for today
              {today?.approval_status === 'pending'
                ? ` and waiting for ${today.expected_approver_name || 'reporting manager'} approval`
                : ' and is approved'}
              . Check-in and check-out are disabled for this day.
            </p>
          ) : todayManualPending && !todayHasLivePunches ? (
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
                <Button
                  type="button"
                  loading={busy}
                  disabled={punchesLocked}
                  onClick={() => void punch('check-in')}
                >
                  Check in
                </Button>
              ) : (
                <>
                  {onBreak ? (
                    <Button
                      type="button"
                      variant="secondary"
                      loading={busy}
                      disabled={punchesLocked}
                      onClick={() => void punch('break-end')}
                    >
                      End break
                    </Button>
                  ) : (
                    <Button
                      type="button"
                      variant="secondary"
                      loading={busy}
                      disabled={punchesLocked}
                      onClick={() => void punch('break-start')}
                    >
                      Start break
                    </Button>
                  )}
                  <Button
                    type="button"
                    loading={busy}
                    disabled={punchesLocked || onBreak}
                    onClick={() => void punch('check-out')}
                  >
                    Check out
                  </Button>
                </>
              )}
            </div>

            <div className="emp-attendance__manual-actions">
              {todayHasLivePunches && !punchesLocked ? (
                <span className="emp-attendance__manual-locked" title="Today already has punches">
                  Today punched
                </span>
              ) : null}
              {punchesLocked ? (
                <span className="emp-attendance__manual-locked">Manual day</span>
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
              <span>Pending approvals</span>
              <strong>{pendingCount}</strong>
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
        </aside>
      </div>

      <section className="emp-attendance__history">
        <header className="emp-attendance__history-head">
          <div>
            <h3>History</h3>
            <p>One row per day. Click a date to see sessions and manual details.</p>
          </div>
        </header>

        {historyRows.length ? (
          <ul className="emp-attendance__list">
            {historyRows.map((row) => (
              <li key={row.date}>
                <button
                  type="button"
                  className="emp-attendance__day-row"
                  onClick={() => setDetailDay(row)}
                >
                  <div className="emp-attendance__list-main">
                    <strong>{formatDate(row.date)}</strong>
                    <span>
                      {formatTime(row.record?.first_check_in)} –{' '}
                      {formatTime(row.record?.last_check_out)}
                    </span>
                    <span className="emp-attendance__day-tags">
                      <em className="emp-attendance__source">{row.entryLabel}</em>
                      {row.approvalLabel ? (
                        <em
                          className={`emp-attendance__status ${approvalClass(row.record?.approval_status)}`}
                        >
                          {row.approvalLabel}
                        </em>
                      ) : null}
                      {row.notice ? (
                        <em className="emp-attendance__status is-warn">{row.notice}</em>
                      ) : null}
                    </span>
                  </div>
                  <div className="emp-attendance__list-meta">
                    <span className="emp-attendance__hours">{formatHours(row.workedHours)}</span>
                    {row.record?.status ? (
                      <em className={`emp-attendance__status ${statusClass(row.record.status)}`}>
                        {STATUS_LABELS[row.record.status] || row.record.status}
                      </em>
                    ) : null}
                  </div>
                </button>
              </li>
            ))}
          </ul>
        ) : (
          <p className="emp-attendance__empty">No attendance records yet.</p>
        )}
      </section>

      <Modal
        open={Boolean(detailDay)}
        title={detailDay ? formatDate(detailDay.date) : 'Day details'}
        onClose={() => setDetailDay(null)}
        size="lg"
        footer={
          <>
            {detailDay?.hasOpenLogout ||
            (detailDay?.hasManual && detailDay.record?.approval_status === 'pending') ? (
              <Button
                type="button"
                variant="secondary"
                onClick={() => {
                  const date = detailDay?.date;
                  setDetailDay(null);
                  if (date) openManual(date, true);
                }}
              >
                {detailDay?.hasOpenLogout ? 'Fix logout' : 'Edit manual entry'}
              </Button>
            ) : null}
            <Button type="button" variant="ghost" onClick={() => setDetailDay(null)}>
              Close
            </Button>
          </>
        }
      >
        {detailDay ? (
          <div className="emp-attendance__day-detail">
            <div className="emp-attendance__day-summary">
              <div>
                <span>Total worked</span>
                <strong>{formatHours(detailDay.workedHours)}</strong>
              </div>
              <div>
                <span>Entry type</span>
                <strong>{detailDay.entryLabel}</strong>
              </div>
              <div>
                <span>Status</span>
                <strong>
                  {detailDay.record?.status
                    ? STATUS_LABELS[detailDay.record.status] || detailDay.record.status
                    : detailDay.hasOpenLogout
                      ? 'No logout'
                      : '—'}
                </strong>
              </div>
              <div>
                <span>Approval</span>
                <strong>{detailDay.approvalLabel || 'Not required'}</strong>
              </div>
            </div>

            {detailDay.notice ? (
              <p className="emp-attendance__banner emp-attendance__banner--info">{detailDay.notice}</p>
            ) : null}

            {detailDay.isLogoutOnlyManual ? (
              <div className="emp-attendance__detail-block">
                <h4>Logout adjustment</h4>
                <p>
                  This day has a live check-in, and logout was submitted manually
                  {detailDay.approvalLabel ? ` (${detailDay.approvalLabel.toLowerCase()})` : ''}.
                </p>
                {detailDay.record?.remarks ? (
                  <p>
                    <strong>Remarks:</strong> {detailDay.record.remarks}
                  </p>
                ) : null}
                {detailDay.record?.expected_approver_name ? (
                  <p>
                    <strong>Approver:</strong> {detailDay.record.expected_approver_name}
                  </p>
                ) : null}
              </div>
            ) : null}

            {detailDay.hasManual && !detailDay.isLogoutOnlyManual ? (
              <div className="emp-attendance__detail-block">
                <h4>Manual entry</h4>
                <p>
                  Full day was entered manually
                  {detailDay.approvalLabel ? ` · ${detailDay.approvalLabel}` : ''}.
                </p>
                {detailDay.record?.remarks ? (
                  <p>
                    <strong>Remarks:</strong> {detailDay.record.remarks}
                  </p>
                ) : null}
                {detailDay.record?.approved_by_name ? (
                  <p>
                    <strong>Reviewed by:</strong> {detailDay.record.approved_by_name}
                    {detailDay.record.approved_at
                      ? ` · ${new Date(detailDay.record.approved_at).toLocaleString()}`
                      : ''}
                  </p>
                ) : detailDay.record?.expected_approver_name ? (
                  <p>
                    <strong>Approver:</strong> {detailDay.record.expected_approver_name}
                  </p>
                ) : null}
                {detailDay.record?.approval_remarks ? (
                  <p>
                    <strong>Review notes:</strong> {detailDay.record.approval_remarks}
                  </p>
                ) : null}
              </div>
            ) : null}

            {detailDay.hasLive ? (
              <div className="emp-attendance__detail-block">
                <h4>Live check-in / check-out</h4>
                <p>Punches recorded from web or other live sources.</p>
              </div>
            ) : null}

            <div className="emp-attendance__detail-block">
              <h4>Sessions ({detailDay.sessions.length})</h4>
              {detailDay.sessions.length ? (
                <ul className="emp-attendance__sessions">
                  {detailDay.sessions.map((session) => (
                    <li key={session.id}>
                      <span className="emp-attendance__session-rail" aria-hidden />
                      <div className="emp-attendance__session-body">
                        <strong>
                          {formatTime(session.check_in)} – {formatTime(session.check_out)}
                          {!session.check_out ? ' (no logout)' : ''}
                        </strong>
                        <span>
                          {SOURCE_LABELS[session.source] || session.source}
                          {session.source === 'manual' ? ' · Manual' : ' · Live'}
                        </span>
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
                        {session.remarks ? <span>Note: {session.remarks}</span> : null}
                      </div>
                      <div className="emp-attendance__list-meta">
                        <span>{formatHours(session.worked_hours)}</span>
                      </div>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="emp-attendance__empty">No sessions for this day.</p>
              )}
            </div>
          </div>
        ) : null}
      </Modal>

      <Modal
        open={manualOpen}
        title={
          manualMode === 'edit'
            ? 'Edit manual attendance'
            : manualMode === 'checkout_adjust'
              ? 'Adjust missing logout'
              : 'Manual attendance'
        }
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
            Check-in, check-out, and remarks are required. After a manual entry is submitted for a
            day, live check-in and check-out are blocked for that day.
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
              disabled={manualMode === 'locked' || adjustingLogout}
              onChange={(event) => setManualCheckIn(event.target.value)}
            />
          </label>
          <label>
            <span>Check out</span>
            <input
              type="time"
              required
              value={manualCheckOut}
              disabled={manualMode === 'locked'}
              onChange={(event) => setManualCheckOut(event.target.value)}
            />
          </label>
          <label className="emp-attendance__manual-full">
            <span>Remarks</span>
            <textarea
              rows={2}
              required
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
