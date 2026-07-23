import { APP_TIMEZONE } from '../constants/timezone';

/** Format a date/time string in IST (or provided timezone). */
export function formatAppDateTime(
  value: string | number | Date | null | undefined,
  timezone: string = APP_TIMEZONE,
  options: Intl.DateTimeFormatOptions = {
    dateStyle: 'medium',
    timeStyle: 'short',
  },
): string | null {
  if (value == null || value === '') {
    return null;
  }

  const date = value instanceof Date ? value : new Date(value);
  if (Number.isNaN(date.getTime())) {
    return null;
  }

  return new Intl.DateTimeFormat('en-IN', { ...options, timeZone: timezone }).format(date);
}

/** Format a date-only value in IST. */
export function formatAppDate(
  value: string | number | Date | null | undefined,
  timezone: string = APP_TIMEZONE,
): string | null {
  return formatAppDateTime(value, timezone, { dateStyle: 'medium' });
}
