import { useEffect, useMemo, useState } from 'react';
import type { Holiday } from '../../types';
import { Modal } from '../ui/Modal';
import './HolidayMonthlyCalendar.css';

const WEEKDAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];

type DayCell = {
  key: string;
  day: number | null;
  iso: string | null;
  holidays: Holiday[];
  isToday: boolean;
};

type HolidayMonthlyCalendarProps = {
  open: boolean;
  year: number;
  holidays: Holiday[];
  onClose: () => void;
  onDayClick: (isoDate: string, holidaysOnDay: Holiday[]) => void;
};

function toIso(year: number, monthIndex: number, day: number): string {
  const month = String(monthIndex + 1).padStart(2, '0');
  const date = String(day).padStart(2, '0');
  return `${year}-${month}-${date}`;
}

function buildMonthDays(
  year: number,
  monthIndex: number,
  byDate: Map<string, Holiday[]>,
): DayCell[] {
  const first = new Date(year, monthIndex, 1);
  const startOffset = (first.getDay() + 6) % 7;
  const daysInMonth = new Date(year, monthIndex + 1, 0).getDate();
  const todayIso = new Date().toISOString().slice(0, 10);
  const cells: DayCell[] = [];

  for (let i = 0; i < startOffset; i += 1) {
    cells.push({ key: `pad-${i}`, day: null, iso: null, holidays: [], isToday: false });
  }

  for (let day = 1; day <= daysInMonth; day += 1) {
    const iso = toIso(year, monthIndex, day);
    cells.push({
      key: iso,
      day,
      iso,
      holidays: byDate.get(iso) || [],
      isToday: iso === todayIso,
    });
  }

  while (cells.length % 7 !== 0) {
    const i = cells.length;
    cells.push({ key: `trail-${i}`, day: null, iso: null, holidays: [], isToday: false });
  }

  return cells;
}

function monthLabel(year: number, monthIndex: number): string {
  return new Date(year, monthIndex, 1).toLocaleDateString(undefined, {
    month: 'long',
    year: 'numeric',
  });
}

export function HolidayMonthlyCalendar({
  open,
  year,
  holidays,
  onClose,
  onDayClick,
}: HolidayMonthlyCalendarProps) {
  const now = new Date();
  const initialMonth = now.getFullYear() === year ? now.getMonth() : 0;
  const [monthIndex, setMonthIndex] = useState(initialMonth);

  useEffect(() => {
    if (!open) return;
    setMonthIndex(now.getFullYear() === year ? now.getMonth() : 0);
    // Reset only when the modal opens or year changes.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open, year]);

  const byDate = useMemo(() => {
    const map = new Map<string, Holiday[]>();
    for (const holiday of holidays) {
      const list = map.get(holiday.date) || [];
      list.push(holiday);
      map.set(holiday.date, list);
    }
    return map;
  }, [holidays]);

  const days = useMemo(
    () => buildMonthDays(year, monthIndex, byDate),
    [year, monthIndex, byDate],
  );

  return (
    <Modal
      open={open}
      title="Holiday calendar"
      onClose={onClose}
      size="lg"
      bodyClassName="modal-panel__body--tooltip-safe"
    >
      <div className="holiday-monthly">
        <div className="holiday-monthly__nav">
          <button
            type="button"
            className="holiday-monthly__nav-btn"
            aria-label="Previous month"
            disabled={monthIndex <= 0}
            onClick={() => setMonthIndex((value) => Math.max(0, value - 1))}
          >
            ‹
          </button>
          <h3>{monthLabel(year, monthIndex)}</h3>
          <button
            type="button"
            className="holiday-monthly__nav-btn"
            aria-label="Next month"
            disabled={monthIndex >= 11}
            onClick={() => setMonthIndex((value) => Math.min(11, value + 1))}
          >
            ›
          </button>
        </div>

        <div className="holiday-monthly__weekdays">
          {WEEKDAYS.map((day) => (
            <span key={day}>{day}</span>
          ))}
        </div>

        <div className="holiday-monthly__days">
          {days.map((cell) => {
            if (!cell.iso || cell.day == null) {
              return <div key={cell.key} className="holiday-monthly__day holiday-monthly__day--empty" />;
            }
            const hasHoliday = cell.holidays.length > 0;
            const holidayNames = cell.holidays.map((item) => item.name).join(', ');
            const label = hasHoliday ? holidayNames : `Add holiday on ${cell.iso}`;
            return (
              <button
                key={cell.key}
                type="button"
                className={[
                  'holiday-monthly__day',
                  hasHoliday ? 'holiday-monthly__day--marked' : '',
                  cell.isToday ? 'holiday-monthly__day--today' : '',
                ]
                  .filter(Boolean)
                  .join(' ')}
                aria-label={label}
                data-tooltip={hasHoliday ? holidayNames : undefined}
                onClick={() => onDayClick(cell.iso!, cell.holidays)}
              >
                <span className="holiday-monthly__day-num">{cell.day}</span>
                {hasHoliday ? (
                  <span className="holiday-monthly__day-dot" aria-hidden />
                ) : null}
              </button>
            );
          })}
        </div>
      </div>
    </Modal>
  );
}

export function CalendarIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      viewBox="0 0 24 24"
      width="18"
      height="18"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      aria-hidden
    >
      <rect x="3.5" y="5" width="17" height="15" rx="2" />
      <path d="M3.5 9.5h17M8 3.5v3M16 3.5v3" />
    </svg>
  );
}
